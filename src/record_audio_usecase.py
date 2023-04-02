from datetime import datetime, timedelta
import logging
from pathlib import Path
from typing import NoReturn
from src.http_clint import fetch_stream_chunk
from src.models import RecordingSchedule, RecordingTask
import asyncio
import re

from src.record_audio_client import StreamRecorder

logger = logging.getLogger(__name__)


async def start_recording_loop(
    recording_schedules: list[RecordingSchedule],
    stream_recorder: StreamRecorder,
) -> NoReturn:

    while True:
        current_time: datetime = datetime.utcnow()

        # Get list of next recording task for each schedule
        recording_tasks: list[RecordingTask] = get_next_recording_tasks(
            recording_schedules, current_time
        )

        # Get the earliest recording task among all schedules
        next_recording_task: RecordingTask = min(
            recording_tasks, key=lambda x: x.start_time
        )

        # Wait until task should be started
        wait_duration: timedelta = next_recording_task.start_time - current_time

        logger.info(f"Found next recording task: {next_recording_task}")
        logger.info(f"Waiting for {wait_duration} until recording starts...")

        await asyncio.sleep(wait_duration.total_seconds())

        logger.info(f"Recording started for task: {next_recording_task.id}")
        
        # Produce file path
        output_file_path: Path = get_file_path(current_time, next_recording_task, stream_recorder.audio_format)
        
        
        # Record stream and catch any exceptions
        try:
            # "wb" is write binary
            with open(output_file_path, "wb") as f:  # XXX: Factory as dep?
                stream_recorder.record(next_recording_task.duration, f, fetch_stream_chunk)
            logger.info(f"Recording complete. Saved at: {output_file_path}")
        except Exception as e:
            logger.error(f"Recording failed: {next_recording_task}", exc_info=True)
            continue


# Produce a recording task from each recording schedule
def get_next_recording_tasks(
    recording_schedules: list[RecordingSchedule], current_time: datetime
) -> list[RecordingTask]:
    recording_tasks: list[RecordingTask] = []
    recording_tasks = [
        recording_schedule.get_next_recording_task(current_time)
        for recording_schedule in recording_schedules
    ]
    return recording_tasks

# Get full file path for the output of this recording task
def get_file_path(current_time: datetime, task: RecordingTask, audio_format: str) -> Path:
    filename = get_file_name(current_time, task)
    return task.output_dir / (filename + "." + audio_format)

# Create file name with date, start time, end time and title
def get_file_name(current_time: datetime, task: RecordingTask) -> str:
    # Replace all non-alphanumeric characters with underscore and lowercase
    title = re.sub(r"[^a-zA-Z0-9]", "_", task.title).lower()

    date = current_time.strftime("%Y-%m-%d")
    start_time = task.start_time.strftime("%H_%M")
    actual_time = current_time.strftime("%H_%M")
    end_time = task.end_time.strftime("%H_%M")

    return f"{date}__{start_time}_({actual_time})-{end_time}_{title}"
