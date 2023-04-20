import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Type, TypeVar, Union, overload

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
    config = _parse_data(data)
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
def _parse_data(data: dict[str, Any]) -> AppConfig:
    try:
        # Parse stream url
        stream_url_value: str = get_value_or_fail(data, "stream_url")
        stream_url = ValidUrl(stream_url_value)
        if stream_url.endswith(".m3u8"):
            audio_format: str = "mp4"
        else:
            audio_format: str = "mp3"

        # Parse output directory
        base_output_dir_value: str = get_value_or_fail(data, "output_dir")
        base_output_dir = Path(base_output_dir_value)
        # Parse time zone
        time_zone: str = get_value_or_fail(data, "time_zone")
        user_timezone = pendulum.timezone(time_zone)  # type: ignore

        # Parse recording schedules
        schedules: list[dict[str, Any]] = get_value_or_fail(
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
        raise ConfigError(f"Missing key: {e}") from e
    except ValueError as e:
        raise ConfigError(f"Invalid value: {e}") from e


# Parses a single recording schedule
def _parse_schedule(
    base_output_dir: Path,
    user_timezone: Timezone,
    schedule_raw: dict[str, str],
    audio_format: str,
) -> RecordingSchedule:
    title = get_value_or_fail(schedule_raw, "title")
    schedule_dir = base_output_dir / slugify(title)

    start_time, duration = _parse_start_time_and_duration(
        get_value_or_fail(schedule_raw, "start_timeofday"),
        get_value_or_fail(schedule_raw, "end_timeofday"),
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
        **kwargs,
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
        raise ConfigError(f"Invalid time format for start_time or end_time")

    # Calculate duration in local time (to ensure possible midnight rollover is handled correctly)
    duration = utils.get_duration_btw_times(start_time_local, end_time_local)

    # Now we can convert the start time to UTC
    start_time_utc = utils.convert_time_to_utc(
        start_time_local, from_time_zone=user_timezone
    )
    return start_time_utc, duration


T = TypeVar("T")


# XXX: Make a dict wrapper/extension?
# Case no type specified (assume str)
@overload
def get_value_or_fail(d: Dict[str, Any], key: str) -> str:
    ...


# Case type specified
@overload
def get_value_or_fail(d: Dict[str, Any], key: str, required_type: Type[T]) -> T:
    ...


# Gets the value of key, and fails if not present (None or empty) or not expected type
def get_value_or_fail(
    d: dict[str, Any], key: str, required_type: type[T] = str
) -> Union[T, str]:
    if key not in d:
        raise KeyError(f"Key '{key}' not found in the dictionary")

    value = d[key]
    if value is None or len(value) == 0:
        raise ValueError(f"Value for key '{key}' is None or empty")

    if not isinstance(value, required_type):
        raise TypeError(
            f"Value for key '{key}' is not of the required type '{required_type.__name__}'"
        )

    return value
