import asyncio
import logging
import os
import re
from pathlib import Path
from typing import Any, NoReturn, Optional

import yaml
from pendulum.datetime import DateTime
from pendulum.duration import Duration
from pydantic import DirectoryPath

from src import audio_storage, utils
from src.audio_storage import AudioStorageAdapter
from src.audio_stream import HttpAudioStreamAdapter
from src.models import RecordingSchedule, RecordingTask, ValidUrl

logger = logging.getLogger(__name__)


class RecordAudioService:  # TODO:
    def __init__(self) -> None:
        super().__init__()
        pass


# Start recording service, blocking until program is terminated
async def start(
    recording_schedules: list[RecordingSchedule],
    stream_url: ValidUrl,
    audio_stream_adapter: HttpAudioStreamAdapter,
    audio_storage_adapter: AudioStorageAdapter,
    timeprovider: utils.TimeProvider | None = None,
) -> NoReturn:
    if timeprovider is None:
        timeprovider = utils.TimeProvider()

    logger.info(
        f"Recording service started with stream '{stream_url}' and {len(recording_schedules)} schedules"
    )

    while True:
        current_time: DateTime = timeprovider.get_current_time()
        # Get the next recording task
        next_recording_task: RecordingTask = get_next_task(
            recording_schedules, current_time
        )
        logger.info(f"Found next recording task: {next_recording_task}")

        # Wait until task should be started
        wait_duration: Duration = next_recording_task.time_period.get_time_until_start(
            current_time
        )

        if wait_duration > Duration(seconds=0):  # type: ignore
            logger.info(f"Waiting for {wait_duration} until recording starts...")
            await asyncio.sleep(wait_duration.seconds)  # type: ignore
        else:
            logger.info(
                f"Recording task {next_recording_task} is already due. Recording now..."
            )

        try:
            await record_audio_segment(
                next_recording_task,
                next(
                    schedule
                    for schedule in recording_schedules
                    if schedule.id == next_recording_task.recording_schedule_id
                ),
                audio_storage_adapter,
                audio_stream_adapter,
                stream_url,
                current_time,
            )

        except Exception as e:
            logger.error(
                f"Recording failed (will continue to next): {next_recording_task}",
                exc_info=True,
            )
            continue


def get_next_task(recording_schedules: list[RecordingSchedule], current_time: DateTime):
    # Get list of next recording task for each schedule
    recording_tasks: list[RecordingTask] = _get_next_recording_tasks(
        recording_schedules, current_time
    )

    # Get the earliest recording task among all schedules
    next_recording_task: RecordingTask = min(
        recording_tasks, key=lambda x: x.time_period.start
    )
    return next_recording_task


async def record_audio_segment(
    recording_task: RecordingTask,
    recording_schedule: RecordingSchedule,
    audio_storage_adapter: audio_storage.AudioStorageAdapter,
    audio_stream_adapter: HttpAudioStreamAdapter,
    stream_url: ValidUrl,
    current_time: DateTime,
    time_provider: Optional[utils.TimeProvider] = None,
):
    if time_provider is None:
        time_provider = utils.TimeProvider()
    # Ensure output directory of recording task exists
    ensure_dir_with_metadata(
        recording_task.output_dir, metadata=recording_schedule.metadata
    )

    # Produce file path
    output_file_path: Path = get_file_path(
        current_time, recording_task, audio_storage_adapter.audio_format
    )

    logger.info(
        f"Starting recording for task: {recording_task.id}. Output file: {output_file_path}"
    )

    # Get audio data iterator from the live stream
    audio_data_iterator = audio_stream_adapter.get_audio_data(
        stream_url,
        utils.CountdownTimer(
            recording_task.time_period.end, time_provider=time_provider
        ),
    )

    await audio_storage_adapter.store_audio_data(
        audio_data_iterator, output_file_path, recording_schedule
    )
    logger.info(f"Recording complete. Saved at: {output_file_path}")


# Produce a recording task from each recording schedule
def _get_next_recording_tasks(
    recording_schedules: list[RecordingSchedule], current_time: DateTime
) -> list[RecordingTask]:
    recording_tasks: list[RecordingTask] = []
    recording_tasks = [
        recording_schedule.create_next_recording_task(current_time)
        for recording_schedule in recording_schedules
    ]
    return recording_tasks


# Get full file path for the output of this recording task
def get_file_path(
    current_time: DateTime, task: RecordingTask, audio_format: str
) -> Path:
    filename = get_file_name(current_time, task)
    return task.output_dir / (filename + "." + audio_format)


# Create file name with date, start time, end time and title
def get_file_name(current_time: DateTime, task: RecordingTask) -> str:
    # Replace all non-alphanumeric characters with underscore and lowercase
    title = re.sub(r"[^a-zA-Z0-9]", "-", task.title).lower()

    date = current_time.strftime("%Y-%m-%d")
    start_time = task.time_period.start.strftime("%H%M")
    end_time = task.time_period.end.strftime("%H%M")

    # Url friendly file name
    return f"{date}--{start_time}-{end_time}--{title}--{task.id}"


def ensure_dir_with_metadata(
    dir_value: Path, metadata: dict[str, Any]
) -> DirectoryPath:
    # Create dir for audio files if it doesn't exist
    os.makedirs(dir_value, exist_ok=True)

    # Test if we have write access to the output directory
    if not os.access(dir_value, os.W_OK | os.X_OK):
        raise IOError(f"Missing write permissions to directory {dir_value}")

    # Create a file with the meta data if it doesn't exist.
    metadata_file = dir_value / "metadata.yml"
    if not metadata_file.exists():
        with open(metadata_file, "w") as f:
            yaml.dump(metadata, f, allow_unicode=True)

    return dir_value
