from datetime import date, datetime, timedelta, time
import logging
import os
from src.models import Config, RecordingPeriod
import requests
import logging
import asyncio
from src.models import Config

logger = logging.getLogger(__name__)


async def start_recording(config: Config):

    recording_times_increasing = sorted(
        config.recording_periods, key=lambda rt: rt.start_time)

    while True:
        # Find the next start time
        now: datetime = datetime.utcnow()
        next_recording = next(
            (recording for recording in recording_times_increasing if recording.start_time > now.time()), None)

        if next_recording:
            # Has recording today, wait until the next start time today
            wait_duration: timedelta = datetime.combine(
                now.date(), next_recording.start_time) - now
        else:
            # No recording today, wait until the next day
            next_recording = recording_times_increasing[0]
            wait_duration: timedelta = datetime.combine(
                now.date() + timedelta(days=1), next_recording.start_time) - now

        logger.info(
            f"Next recording: '{next_recording.name}' from {next_recording.start_time} to {next_recording.end_time}. Waiting {wait_duration} ...")

        await asyncio.sleep(wait_duration.total_seconds())

        logger.info("Starting recording...")

        filepath = record_audio(
            next_recording, config.stream_url, config.output_directory)

        logger.info(f"Recording complete: {filepath}")

# Records audio until end time is reached


def record_audio(recording_period: RecordingPeriod, stream_url: str, output_directory: str) -> str:
    recording_name = recording_period.name.replace(" ", "_").lower()
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
