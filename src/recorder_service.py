from datetime import date, datetime, timedelta, time
import logging
import os
from src.models import Config, RecordingPeriod
import requests
import asyncio
from src.models import Config
# from src.utils import load_config
import re

logger = logging.getLogger(__name__)


async def start_recording(config: Config):

    # Sort the recording times by start time
    recording_times_sorted = sorted(
        config.recording_periods, key=lambda period: period.start_time)

    while True:
        # Find the next start time
        now: datetime = datetime.utcnow()
        # Find first recording with start time after current time of day
        next_recording = next(
            (recording for recording in recording_times_sorted if recording.start_time > now.time()), None)

        if next_recording:
            # Has recording today, wait until the next start time today
            wait_duration: timedelta = datetime.combine(
                now.date(), next_recording.start_time) - now
        else:
            # No recording today, wait until the next day.
            next_recording = recording_times_sorted[0] # First recording of the day tomorrow must be the first in the list
            wait_duration: timedelta = datetime.combine(
                now.date() + timedelta(days=1), next_recording.start_time) - now

        logger.info(
            f"Next recording: '{next_recording.name}' from {next_recording.start_time} to {next_recording.end_time}. Waiting {wait_duration} ...")

        await asyncio.sleep(wait_duration.total_seconds())

        logger.info("Starting recording...")

        filepath = record_audio(
            next_recording, config.stream_url, config.output_directory)

        logger.info(f"Recording complete: {filepath}")

# Records one recording period
def record_audio(recording_period: RecordingPeriod, stream_url: str, output_directory: str) -> str:
    # Replace all non-alphanumeric characters with underscore and lowercase
    recording_name = re.sub(r'[^a-zA-Z0-9]', '_', recording_period.name).lower()
    filename = f"{datetime.utcnow().strftime('%Y-%m-%d__%H-%M-%S')}_{recording_name}.mp3"

    filepath = os.path.join(output_directory, filename)
    # Send a GET request to the stream URL to initiate the stream
    with requests.get(stream_url, stream=True) as livestream_response:
        # Write to audio file then check if recording time is over
        with open(filepath, 'wb') as f:
            for chunk in livestream_response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                if datetime.utcnow().time() > recording_period.end_time:
                    break

    return filepath
