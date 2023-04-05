from dataclasses import dataclass
from datetime import time
import json
import logging
import os
from typing import Any
from src.models import RecordingSchedule
from pathlib import Path
from pydantic import DirectoryPath, HttpUrl
from slugify import slugify

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class AppConfig:
    stream_url: HttpUrl
    output_directory: DirectoryPath
    recording_schedules: list[RecordingSchedule]

    def __post__init__(self):
        if not self.stream_url:
            raise ValueError("Stream URL cannot be empty")
        if not self.output_directory:
            raise ValueError("Output directory cannot be empty")
        if not self.recording_schedules:
            raise ValueError("Recording periods cannot be empty")


def from_json(file_path: Path) -> AppConfig:
    logger.info(f"Loading config file from JSON file: {file_path}")

    data = _read_json(file_path)
    config = _create_config(data)
    logger.info("Config loaded successfully")
    return config


def _read_json(file_path: Path) -> dict[str, Any]:

    try:
        with open(file_path, "r") as json_file:
            return json.load(json_file)

    except FileNotFoundError as e:
        raise ConfigError(f"File not found: {file_path}") from e
    except json.decoder.JSONDecodeError as e:
        raise ConfigError(f"Invalid JSON formatting in config file: {e}") from e


# Parses json string into AppConfig object
def _create_config(data: dict[str, Any]) -> AppConfig:
    try:
        schedules = data["recording_schedules"]
        stream_url_value = data["stream_url"]
        base_output_dir_value = data["output_dir"]

        stream_url = HttpUrl(stream_url_value, scheme="http")
        base_output_dir = Path(base_output_dir_value)

        recording_schedules: list[RecordingSchedule] = []
        for schedule in schedules:
            title = schedule["title"].title()
            schedule_dir = base_output_dir / slugify(title)

            # Convert the start time and end time in format HH:MM to datetime
            start_time = time.fromisoformat(schedule["start_timeofday"])
            end_time = time.fromisoformat(schedule["end_timeofday"])
            recording_period = RecordingSchedule(
                title, start_time, end_time, schedule_dir
            )
            recording_schedules.append(recording_period)
        return AppConfig(stream_url, base_output_dir, recording_schedules)
    except KeyError as e:
        raise ConfigError(f"Missing key: {e}") from e
