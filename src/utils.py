from datetime import time
import json
import logging

from src.models import Config, RecordingPeriod
logger = logging.getLogger(__name__)


def load_config(config_path: str) -> Config:
    logger.info(f"Loading config file from path: {config_path}")

    with open(config_path) as json_file:

        try:
            data = json.load(json_file)
            stream_url = data['stream_url']

            recordings = data['recording_periods']
            output_directory = data['output_dir']

            recording_times: list[RecordingPeriod] = []

            for recording in recordings:
                # Convert the start time and end time in format HH:MM to datetime
                start_time = time.fromisoformat(recording['start_time_utc'])
                end_time = time.fromisoformat(recording['end_time_utc'])
                recording_time = RecordingPeriod(
                    recording['name'], start_time, end_time)
                recording_times.append(recording_time)

        except KeyError as e:
            raise KeyError(f"Missing key {e} in config file") from e
        except json.decoder.JSONDecodeError as e:
            raise ValueError(
                f"Invalid JSON formatting in config file: {e}") from e

    logger.info("Config loaded successfully")

    return Config(stream_url, output_directory, recording_times)
