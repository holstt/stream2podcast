from dataclasses import dataclass
from datetime import time
import json
import logging
import os
from typing import Any
from src.models import RecordingSchedule
from pathlib import Path
from pydantic import DirectoryPath, HttpUrl

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AppConfig:
    stream_url: HttpUrl
    output_directory: DirectoryPath
    recording_schedules: list[RecordingSchedule]

    def __post__init__(self):
        if not self.stream_url:
            raise ValueError("Stream URL must not be empty")
        if not self.output_directory:
            raise ValueError("Output directory must not be empty")
        if not self.recording_schedules:
            raise ValueError("Recording periods must not be empty")


def parse(config_file_path_value: str) -> AppConfig:
    file_path = Path(config_file_path_value)

    if not file_path.exists():
        raise IOError(f"No config file found at path: {file_path}")

    logger.info(f"Loading config file from path: {file_path}")

    with open(file_path, "r") as json_file:
        try:
            data = json.load(json_file)
            config = parse_json(data)
            logger.info("Config loaded successfully")
            return config

        except json.decoder.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON formatting in config file: {e}") from e


# Parses json string into AppConfig object
def parse_json(data: dict[str, Any]) -> AppConfig:
    try:
        recordings = data["recording_schedules"]
        stream_url_value = data["stream_url"]
        output_directory_value = data["output_dir"]

        stream_url = HttpUrl(stream_url_value, scheme="http")
        output_directory = create_output_dir(output_directory_value)

        recording_schedules: list[RecordingSchedule] = []

        for recording in recordings:
            # Convert the start time and end time in format HH:MM to datetime
            start_time = time.fromisoformat(recording["start_timeofday"])
            end_time = time.fromisoformat(recording["end_timeofday"])
            recording_period = RecordingSchedule(
                recording["title"], start_time, end_time, output_directory
            )
            recording_schedules.append(recording_period)
        return AppConfig(stream_url, output_directory, recording_schedules)
    except KeyError as e:
        raise KeyError(f"Missing key {e} in config file") from e


def create_output_dir(output_dir_value: str) -> DirectoryPath:
    output_dir = Path(output_dir_value)

    if not output_dir.is_dir():
        raise IOError(
            f"The specified directory '{output_dir_value}' is not a directory"
        )
    # Create output dir
    if not output_dir.exists():
        logging.info(f"Creating output directory '{output_dir_value}'")
        os.mkdir(output_dir_value)
    # We test if we have write access to the output directory
    elif not os.access(output_dir, os.W_OK | os.X_OK):
        raise IOError(
            f"Missing write permissions to output directory {output_dir_value}"
        )

    return output_dir
