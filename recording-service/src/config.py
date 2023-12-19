import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Type, TypeVar, Union, overload

import pendulum
import yaml
from pendulum import Duration, Time  # type: ignore
from pendulum.parser import parse as pendulum_parse
from pendulum.tz.timezone import Timezone
from slugify import slugify

from src import utils
from src.models import RecordingSchedule, ValidUrl

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    pass


class LoadConfigFileError(ConfigError):
    pass


class ParseConfigError(ConfigError):
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
    config = _parse_data(data)

    logger.info("Config loaded successfully")
    return config


# Returns the raw data from the YAML file at the given path
def _read_yaml(file_path: Path) -> dict[str, Any]:
    try:
        with open(file_path, "r") as f:
            data = yaml.safe_load(f)

    except FileNotFoundError as e:
        raise LoadConfigFileError(f"Configuration file not found: {file_path}") from e
    except IsADirectoryError as e:
        raise LoadConfigFileError(
            f"Configuration file is a directory: {file_path}"
        ) from e
    except yaml.YAMLError as e:
        raise LoadConfigFileError(f"Invalid YAML file: {file_path}") from e
    if not isinstance(data, dict):
        raise LoadConfigFileError(f"Invalid YAML file: {file_path}")

    return data  # type: ignore


# Parses json string into AppConfig object
def _parse_data(data: dict[str, Any]) -> AppConfig:
    try:
        # Parse stream url
        stream_url_value: str = utils.get_typed_value_or_fail(data, "stream_url")
        stream_url = ValidUrl(stream_url_value)
        if stream_url.endswith(".m3u8"):
            audio_format: str = "mp4"
        else:
            audio_format: str = "mp3"

        # Parse output directory
        base_output_dir_value: str = utils.get_typed_value_or_fail(data, "output_dir")
        base_output_dir = Path(base_output_dir_value)
        # Parse time zone
        time_zone: str = utils.get_typed_value_or_fail(data, "time_zone")
        user_timezone = pendulum.timezone(time_zone)  # type: ignore

        # Parse recording schedules
        schedules: list[Any] = utils.get_typed_value_or_fail(
            data, "recording_schedules", list
        )

        recording_schedules: list[RecordingSchedule] = []
        for schedule in schedules:
            recording_schedule = _parse_schedule(
                base_output_dir, user_timezone, schedule, audio_format
            )
            recording_schedules.append(recording_schedule)

        # Everything parsed successfully, return the config object
        return AppConfig(stream_url, base_output_dir, recording_schedules)
    except KeyError as e:
        raise ParseConfigError(f"Missing key: {e}") from e
    except ValueError as e:
        raise ParseConfigError(f"Invalid value: {e}") from e


# Parses a single recording schedule
def _parse_schedule(
    base_output_dir: Path,
    user_timezone: Timezone,
    schedule_raw: Any,
    audio_format: str,
) -> RecordingSchedule:
    title = utils.get_typed_value_or_fail(schedule_raw, "title")
    schedule_dir = base_output_dir / slugify(title)

    start_time, duration = _parse_start_time_and_duration(
        utils.get_typed_value_or_fail(schedule_raw, "start_timeofday"),
        utils.get_typed_value_or_fail(schedule_raw, "end_timeofday"),
        user_timezone,
    )

    # Get optional properties
    description = schedule_raw.get("description", None)
    image_url = (
        ValidUrl(schedule_raw["image_url"])
        if schedule_raw.get("image_url", None)
        else None
    )
    frequency = schedule_raw.get("frequency", None)

    # Pass only if frequency if has value
    # XXX: Hack to avoid duplicate instance init. Better way?
    kwargs = {}
    if frequency:
        kwargs["frequency"] = frequency

    recording_schedule = RecordingSchedule(
        title,
        start_time,
        duration,
        audio_format,
        schedule_dir,
        schedule_raw,
        description,
        image_url,
        **kwargs,  # type: ignore
    )

    return recording_schedule


# Gets the start time (UTC) and duration from the raw start and end times
def _parse_start_time_and_duration(
    start_time_local_val: str, end_time_local_val: str, user_timezone: Timezone
) -> tuple[Time, Duration]:
    # Convert the start time and end time in format HH:MM to datetime
    start_time_local = pendulum_parse(start_time_local_val, exact=True)
    end_time_local = pendulum_parse(end_time_local_val, exact=True)

    # Ensure the time could be parsed as a time of day
    if not isinstance(start_time_local, Time) or not isinstance(end_time_local, Time):
        raise ParseConfigError(f"Invalid time format for start_time or end_time")

    # Calculate duration in local time (to ensure possible midnight rollover is handled correctly)
    duration = utils.get_duration_btw_times(start_time_local, end_time_local)

    # Now we can convert the start time to UTC
    start_time_utc = utils.convert_time_to_utc(
        start_time_local, from_time_zone=user_timezone
    )
    return start_time_utc, duration
