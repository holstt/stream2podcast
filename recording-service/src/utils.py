import argparse
import logging
import time
from datetime import datetime
from typing import Any, Dict, Type, TypeVar, Union, overload

import pendulum
from pendulum import DateTime, Duration, Period, Time  # type: ignore
from pendulum.tz import timezone
from pendulum.tz.timezone import Timezone  # type: ignore

logger = logging.getLogger(__name__)


def read_config_path():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "-c",
        "--config",
        required=False,
        help="Path of json config file",
        default="config.json",
    )
    args = vars(ap.parse_args())

    # Get config from args
    config_file_path = args["config"]

    return config_file_path


def setup_logging(level: int = logging.INFO):
    logging.basicConfig(
        level=level,
        format="[%(asctime)s] [%(levelname)s] %(name)-25s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.Formatter.converter = time.gmtime  # Use UTC


# Replaces time component while keeping the date AND timezone
def replace_time_in_datetime(dt: DateTime, time: Time) -> DateTime:
    # NB: We do not use DateTime.combine from pendulum as it will ignore the timezone...
    return pendulum.instance(datetime.combine(dt.date(), time), tz=dt.timezone)


# Converts a time in the current timezone to UTC # XXX: Dangerous if results in a different day... (e.g. 23:00 -> 04:00)
def convert_time_to_utc(time: Time, from_time_zone: Timezone) -> Time:
    return (
        replace_time_in_datetime(pendulum.today(from_time_zone), time)
        .astimezone(timezone("UTC"))
        .time()
    )


def get_duration_btw_times(start_time_local: Time, end_time_local: Time) -> Duration:
    if start_time_local < end_time_local:
        # Regular case, start and end time are on the same day
        duration = end_time_local.diff(start_time_local)
    else:
        # Crossing midnight case, end time should be the time next day
        date = get_utc_now()  # Create a random date
        # For this date, replace the time with the start and end time, but add a day to the end time, then calc duration
        start_dt = replace_time_in_datetime(dt=date, time=start_time_local)
        end_dt = replace_time_in_datetime(dt=date, time=end_time_local).add(days=1)
        duration = start_dt.diff(end_dt).as_interval()
    return duration


# ALWAYS use this to get current time.
def get_utc_now() -> DateTime:
    return pendulum.now(timezone("UTC"))


# A specific time period with a start and end datetime
class TimePeriod(Period):
    @property
    def start(self) -> DateTime:
        return self._start  # type: ignore

    @property
    def end(self) -> DateTime:
        return self._end  # type: ignore

    # Overwrite to ensure DateTime is used
    def __init__(self, start: DateTime, end: DateTime, absolute: bool = False) -> None:
        super().__init__(start, end, absolute)

    def __new__(cls, start: DateTime, end: DateTime, absolute: bool = False):
        return super().__new__(cls, start, end, absolute)

    # Checks whether the period is currently active
    def is_active(self, current_time: DateTime) -> bool:
        return self.start <= current_time and current_time < self.end

    # Duration property
    @property
    def duration(self) -> Duration:
        return self.as_interval()

    # def change_start(self, new_start: DateTime) -> None:
    #     # Ensure new start is before end
    #     if new_start < self.end:
    #         raise ValueError("New start must be before end")
    #     self._start = new_start

    # Time until the start of the period
    def get_time_until_start(self, current_time: DateTime) -> Duration:
        if current_time < self.start:
            return self.start.diff(current_time).as_interval()
        else:
            return Duration(seconds=0)

    # Time until the end of the period
    def get_time_remaining(self, current_time: DateTime) -> Duration:
        # If not started yet, return duration
        if current_time < self.start:
            return self.as_interval()
        # If already expired, return 0
        elif current_time >= self.end:
            return Duration(seconds=0)
        # If in progress, return time remaining
        else:
            return self.end.diff(current_time).as_interval()


class TimeProvider:
    def get_current_time(self) -> DateTime:
        return get_utc_now()


class CountdownTimer:
    def __init__(self, duration: Duration, time_provider: TimeProvider) -> None:
        super().__init__()
        self.duration = duration
        self._time_provider = time_provider
        self._start_time: DateTime | None = None

    def start(self) -> None:
        if self._start_time is not None:
            raise RuntimeError("Timer has already been started")
        self._start_time = self._time_provider.get_current_time()

    def get_time_remaining(self) -> Duration:
        if self._start_time is None:
            raise RuntimeError("Timer has not been started")

        # How long time since start
        time_elapsed = (
            self._time_provider.get_current_time().diff(self._start_time).as_interval()
        )
        time_left = self.duration - time_elapsed

        # If expired, return 0
        if time_left < Duration(seconds=0):
            return Duration(seconds=0)

        return time_left

    # Whether the timer has expired
    def is_expired(self) -> bool:
        return self.get_time_remaining() == Duration(seconds=0)


T = TypeVar("T")


# XXX: Make a dict wrapper/extension?
# Case no type specified (assume str)
@overload
def get_typed_value_or_fail(d: Dict[str, Any], key: str) -> str:
    ...


# Case type specified
@overload
def get_typed_value_or_fail(d: Dict[str, Any], key: str, required_type: Type[T]) -> T:
    ...


# Gets the value of key, and fails if not present (None or empty) or not expected type
def get_typed_value_or_fail(
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
