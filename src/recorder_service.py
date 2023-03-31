from datetime import datetime, timedelta
import time
import logging
import os
from pathlib import Path
from typing import NoReturn
from pydantic import DirectoryPath, HttpUrl
from src.models import RecordingSchedule, RecordingTask
import requests
import asyncio
import re
import http.client

logger = logging.getLogger(__name__)

# http.client.HTTPConnection.debuglevel = 1


async def start_recording_loop(
    stream_url: HttpUrl,
    recording_schedules: list[RecordingSchedule],
) -> NoReturn:

    while True:
        # Find the next start time
        current_time: datetime = datetime.utcnow()

        # Get list of next recording task for each schedule
        recording_tasks: list[RecordingTask] = produce_next_recording_tasks(
            recording_schedules, current_time
        )

        # Get the earliest recording task among all schedules
        next_recording_task: RecordingTask = min(
            recording_tasks, key=lambda x: x.start_time
        )

        # Wait until task should be started
        wait_duration: timedelta = next_recording_task.start_time - current_time

        logger.info(f"Found next recording task: {next_recording_task}")
        logger.info(f"Waiting {wait_duration}...")

        await asyncio.sleep(wait_duration.total_seconds())

        logger.info(f"Recording started for task: {next_recording_task}")
        # Produce file path
        output_file_path: Path = get_file_path(current_time, next_recording_task)

        # Start recording
        record_audio_stream(
            next_recording_task.duration,
            output_file_path,
            stream_url,
        )

        logger.info(f"Recording complete. Saved at: {output_file_path}")


# Produce a recording task from each recording schedule
def produce_next_recording_tasks(
    recording_schedules: list[RecordingSchedule], current_time: datetime
) -> list[RecordingTask]:
    # Create a recording task for each recording period representing the concrete recording times for next recording
    recording_tasks: list[RecordingTask] = []
    recording_tasks = [
        recording_schedule.get_next_recording_task(current_time)
        for recording_schedule in recording_schedules
    ]
    return recording_tasks


def get_file_path(current_time: datetime, task: RecordingTask) -> Path:
    filename = get_file_name(current_time, task)
    return task.output_dir / filename


def get_file_name(current_time: datetime, task: RecordingTask) -> str:
    # Replace all non-alphanumeric characters with underscore and lowercase
    filename = re.sub(r"[^a-zA-Z0-9]", "_", task.title).lower()

    date = current_time.strftime("%Y-%m-%d")
    start_time = task.start_time.strftime("%H_%M")
    actual_time = current_time.strftime("%H_%M")
    end_time = task.end_time.strftime("%H_%M")

    return f"{date}__{start_time}_({actual_time})-{end_time}_{filename}.mp3"


# Records one recording period
def record_audio_stream(
    duration: timedelta, output_file_path: Path, stream_url: HttpUrl
) -> None:
    timestamp_start = time.time()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:100.0) Gecko/20100101 Firefox/100.0",
        "Accept": "audio/webm,audio/ogg,audio/wav,audio/*;q=0.9,application/ogg;q=0.7,video/*;q=0.6,*/*;q=0.5",
    }

    try:
        # Send a GET request to the stream URL to initiate the stream
        with requests.get(
            stream_url, stream=True, headers=headers
        ) as livestream_response:
            livestream_response.raise_for_status()
            chunk_size = 32 * 1024  # Read 32KB at a time
            # Write to audio file then check if recording time is over
            # wb is write binary
            with open(output_file_path, "wb") as f:
                for chunk in livestream_response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                    # Check if recording time is over
                    if (time.time() - timestamp_start) > duration.total_seconds():
                        break
    except requests.HTTPError as e:
        raise RecorderException(
            "Unable to connect to stream. Check your stream URL."
        ) from e


class RecorderException(Exception):
    pass
