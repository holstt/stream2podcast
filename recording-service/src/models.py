import logging
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import validators  # type: ignore
from pendulum import Period  # type: ignore
from pendulum.datetime import DateTime
from pendulum.duration import Duration
from pendulum.time import Time
from typing_extensions import override

from src import utils

logger = logging.getLogger(__name__)


class ValidUrl(str):
    @override
    def __new__(cls, value: str):
        if not validators.url(value):  # type: ignore
            raise ValueError(f"Invalid url: {value}")
        return super().__new__(cls, value)


@dataclass(frozen=True)
class RecordingTask:
    title: str
    time_period: utils.TimePeriod
    output_dir: Path
    recording_schedule_id: uuid.UUID
    id: uuid.UUID = field(init=False, default_factory=lambda: uuid.uuid4())

    @property
    def duration(self) -> Duration:
        return self.time_period.as_interval()


@dataclass(frozen=True)
class RecordingSchedule:
    """A recording schedule defines a daily recording period
       If the start time is later than the end time, it is assumed that the recording spans across midnight.

    Args:
        title (str): The title of the schedule.
        start_timeofday (time): The start time of day for the recording period in UTC.
        end_timeofday (time): The end time of day for the recording period in UTC.
        output_dir (Path): The output directory for recordings made by this schedule.
    """

    title: str
    start_timeofday: Time
    duration: Duration
    # end_timeofday: Time
    output_dir: Path
    metadata: dict[str, Any]

    id: uuid.UUID = field(init=False, default_factory=lambda: uuid.uuid4())
    latest_recording_time: Optional[DateTime] = field(init=False, default=None)

    # Optional
    description: Optional[str] = None
    image_url: Optional[ValidUrl] = None

    def __post_init__(
        self,
    ):
        if not self.title or not self.title.strip():
            raise ValueError("Title cannot be empty")

    def create_next_recording_task(self, current_time: DateTime) -> RecordingTask:
        """Gets the next recording task for this schedule considering the current time.

        Args:
            current_time (datetime): The current time.

        Returns:
            RecordingTask: The next recording task for this schedule.
        """

        period: utils.TimePeriod = self._find_next_period(current_time)

        return RecordingTask(self.title, period, self.output_dir, self.id)

    def _find_next_period(self, current_time: DateTime) -> utils.TimePeriod:

        # Get recording period for today
        start_time_today = utils.replace_time_in_datetime(
            current_time, self.start_timeofday
        )
        end_time_today = start_time_today.add(seconds=self.duration.in_seconds())

        # First, assume recording was started yesterday, are we in the middle of recording? (i.e. when recording spans midnight and end time is today)
        start_time_yesterday = start_time_today.add(days=-1)
        end_time_yesterday = end_time_today.add(days=-1)
        if end_time_yesterday > current_time:
            logger.debug("Recording started yesterday and is still in progress.")
            return utils.TimePeriod(start_time_yesterday, end_time_yesterday)

        # If recording period is in the future, or we are in the middle of it, return today's recording period
        if start_time_today > current_time or end_time_today > current_time:
            logger.debug("Recording is in the future or in progress.")
            return utils.TimePeriod(start_time_today, end_time_today)

        # Else, recording is in the past, return tomorrow's recording period
        logger.debug("Recording is in the past.")
        return utils.TimePeriod(
            start_time_today.add(days=1), end_time_today.add(days=1)
        )
