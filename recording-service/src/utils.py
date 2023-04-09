import argparse
import logging
import time
from datetime import datetime

import pendulum
from pendulum import Date, DateTime, Duration, Period, Time  # type: ignore
from pendulum.tz import timezone
from pendulum.tz.timezone import Timezone

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


# Central time management

# def to_local_time(dt: datetime, local_time_zone_key: str) -> datetime:
#     return dt.astimezone(ZoneInfo(local_time_zone_key))


# def to_utc(dt: datetime) -> datetime:
#     return dt.astimezone(timezone.utc)

# Replaces time component while keeping the date and timezone
# NB: Do not use DateTime.combine from pendulum as it will ignore the timezone...
def replace_time_in_datetime(dt: DateTime, time: Time) -> DateTime:
    return pendulum.instance(datetime.combine(dt.date(), time), tz=dt.timezone)


# Converts a time in the current timezone to UTC # XXX: Dangerous if results in a different day... (e.g. 23:00 -> 04:00)
def convert_time_to_utc(time: Time, from_time_zone: Timezone) -> Time:
    return (
        replace_time_in_datetime(pendulum.today(from_time_zone), time)
        .astimezone(timezone("UTC"))
        .time()
    )


# ALWAYS use this to get current time.
def get_utc_now() -> DateTime:
    return pendulum.now("UTC")


class TimePeriod(Period):

    # Time until the start of the period
    def get_time_until_start(self, current_time: DateTime) -> Duration:
        if current_time < self.start:
            return self.start.diff(current_time).as_interval()
        else:
            return Duration(seconds=0)

    # Time until the end of the period
    def get_time_remaining(self, current_time: DateTime) -> Duration:
        if current_time < self.start:
            return self.as_interval()
        elif current_time >= self.end:
            return Duration(seconds=0)
        else:
            return self.end.diff(current_time).as_interval()


class TimeProvider:
    def get_current_time(self) -> DateTime:
        return get_utc_now()


class CountdownTimer:
    def __init__(self, end_time: DateTime | Date, time_provider: TimeProvider) -> None:
        super().__init__()
        self._end_time = end_time
        self._time_provider = time_provider
        self._time_period = None

    def start(self) -> None:
        self._time_period = TimePeriod(
            self._time_provider.get_current_time(), self._end_time
        )

    def get_time_remaining(self) -> Duration:
        if self._time_period is None:
            raise ValueError("Timer has not been started")
        return self._time_period.get_time_remaining(
            self._time_provider.get_current_time()
        )

    # Whether the timer has expired
    def is_expired(self) -> bool:
        return self.get_time_remaining() == Duration(seconds=0)
