import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pendulum
import yaml
from pendulum import Duration, Time  # type: ignore
from pendulum.parser import parse as pendulum_parse
from pendulum.tz.timezone import Timezone  # type: ignore
from slugify import slugify

from src import utils
from src.models import RecordingSchedule, ValidUrl

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class AppConfig:
    stream_url: ValidUrl
    output_directory: Path
    recording_schedules: list[RecordingSchedule]

    def __post__init__(self):
        if not self.recording_schedules:
            raise ValueError("Recording schedules cannot be empty")


# Creates a config object from the YAML file at the given path
def from_yaml(file_path: Path) -> AppConfig:
    logger.info(f"Loading config from YAML file: {file_path}")
    data = _read_yaml(file_path)
    config = _create_config(data)
    logger.info("Config loaded successfully")
    return config


# Returns the raw data from the YAML file at the given path
def _read_yaml(file_path: Path) -> dict[str, Any]:
    try:
        with open(file_path, "r") as f:
            data = yaml.safe_load(f)

    except FileNotFoundError as e:
        raise ConfigError(f"File not found: {file_path}") from e
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML file: {file_path}") from e
    if not isinstance(data, dict):
        raise ConfigError(f"Invalid YAML file: {file_path}")

    return data  # type: ignore


# Parses json string into AppConfig object
def _create_config(data: dict[str, Any]) -> AppConfig:
    try:
        schedules = data["recording_schedules"]

        stream_url_value: str = data["stream_url"]
        base_output_dir_value: str = data["output_dir"]
        time_zone: str = data["time_zone"]
        # raise if empty
        if stream_url_value == "":
            raise ValueError("Stream URL cannot be empty")
        if base_output_dir_value == "":
            raise ValueError("Output directory cannot be empty")
        if time_zone == "":
            raise ValueError("Time zone cannot be empty")

        stream_url = ValidUrl(stream_url_value)
        base_output_dir = Path(base_output_dir_value)
        user_timezone = pendulum.timezone(time_zone)  # type: ignore

        recording_schedules: list[RecordingSchedule] = []
        for schedule in schedules:
            recording_schedule = _create_schedule(
                base_output_dir, user_timezone, schedule
            )
            recording_schedules.append(recording_schedule)
        return AppConfig(stream_url, base_output_dir, recording_schedules)
    except KeyError as e:
        raise ConfigError(f"Missing key: {e}") from e
    except ValueError as e:
        raise ConfigError(f"Invalid value: {e}") from e


def _create_schedule(
    base_output_dir: Path, user_timezone: Timezone, schedule: dict[str, str]
) -> RecordingSchedule:
    title = schedule["title"].title()
    schedule_dir = base_output_dir / slugify(title)

    start_time, duration = get_start_time_and_duration(
        schedule["start_timeofday"], schedule["end_timeofday"], user_timezone
    )

    # Get optional properties
    description = schedule.get("description", None)
    image_url = (
        ValidUrl(schedule["image_url"]) if schedule.get("image_url", None) else None
    )

    recording_schedule = RecordingSchedule(
        title,
        start_time,
        duration,
        schedule_dir,
        schedule,
        description,
        image_url,
    )

    return recording_schedule


def get_start_time_and_duration(
    start_time_local_val: str, end_time_local_val: str, user_timezone: Timezone
) -> tuple[Time, Duration]:
    # Convert the start time and end time in format HH:MM to datetime
    start_time_local = pendulum_parse(start_time_local_val, exact=True)
    end_time_local = pendulum_parse(end_time_local_val, exact=True)

    # Ensure the time could be parsed as a time of day
    if not isinstance(start_time_local, Time) or not isinstance(end_time_local, Time):
        raise ConfigError(f"Invalid time format for start_time or end_time")

    # Calculate duration before converting to UTC
    if start_time_local < end_time_local:
        # Regular case
        duration = end_time_local.diff(start_time_local)
    else:
        # Crossing midnight, end time should be the time next day
        date = utils.get_utc_now()  # Create a random date
        # For this date, replace the time with the start and end time, but add a day to the end time, then calc duration
        start_dt = utils.replace_time_in_datetime(date, start_time_local)
        end_dt = utils.replace_time_in_datetime(date, end_time_local).add(days=1)
        duration = start_dt.diff(end_dt).as_interval()

    start_time = utils.convert_time_to_utc(
        start_time_local, from_time_zone=user_timezone
    )
    return start_time, duration
