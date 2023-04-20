# import datetime
import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import validators  # type: ignore
from croniter import croniter
from pendulum import Date, DateTime, Duration, Period, Time  # type: ignore
from typing_extensions import override

from src import utils
from src.utils import TimePeriod

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
    recording_period: TimePeriod
    base_dir: Path
    audio_format: str
    file_path: Path = field(init=False)  # The file path to save the recording to
    # duration: Duration
    id: uuid.UUID = field(default_factory=lambda: uuid.uuid4())
    # XXX: stream_url?

    def __post_init__(self):
        file_path = self._make_file_path(
            self.base_dir, self.audio_format, self.recording_period, self.id, self.title
        )
        object.__setattr__(self, "file_path", file_path)  # Mutates frozen object

    # TODO: Consider move to FileSystemRepo

    # Get full file path for the output of this recording task
    def _make_file_path(
        self,
        output_dir: Path,
        audio_format: str,
        recording_period: TimePeriod,
        task_id: uuid.UUID,
        title: str,
    ) -> Path:
        filename = self._make_file_name(recording_period, task_id, title)
        return output_dir / (filename + "." + audio_format)

    # Create file name with date, start time, end time and title
    def _make_file_name(
        self, recording_period: TimePeriod, task_id: uuid.UUID, title: str
    ) -> str:
        # Replace all non-alphanumeric characters with underscore and lowercase
        title_str = re.sub(r"[^a-zA-Z0-9]", "-", title).lower()

        date_str = recording_period.start.strftime("%Y-%m-%d")
        start_time_str = recording_period.start.strftime("%H%M")
        end_time_str = recording_period.end.strftime("%H%M")

        # Url friendly file name
        return f"{date_str}--{start_time_str}-{end_time_str}--{title_str}--{task_id}"


@dataclass(frozen=True)
class RecordingSchedule:
    """A recording schedule defines a daily recording period
       If the start time is later than the end time, it is assumed that the recording spans across midnight.

    Args:
        title (str): The title of the schedule.
        start_timeofday (time): The start time of day for the recording period in UTC.
        output_dir (Path): The output directory for recordings made by this schedule.
    """

    title: str
    start_timeofday: Time
    duration: Duration
    audio_format: str
    output_dir: Path
    metadata: dict[str, Any]

    id: uuid.UUID = field(init=False, default_factory=lambda: uuid.uuid4())

    # Optional
    description: Optional[str] = None
    image_url: Optional[ValidUrl] = None
    frequency: str = "*"  # Defaults to "daily" cron expression

    @property
    def end_timeofday(self) -> Time:
        return self.start_timeofday.add(seconds=self.duration.in_seconds())

    # Converts the schedule frequency to a cron expression
    @property
    def cron_expression(self) -> str:
        return f"{self.start_timeofday.minute} {self.start_timeofday.hour} * * {self.frequency}"

    def __post_init__(
        self,
    ):
        if not len(self.title.strip()):
            raise ValueError("Title cannot be empty")

        # Remove any spaces to adhere to cron expression format
        object.__setattr__(
            self, "frequency", self.frequency.replace(" ", "")
        )  # Mutates frozen object

    # Gets the current or next task.
    def get_current_or_next_task(self, recording_start_time: DateTime) -> RecordingTask:
        recording_period = self.resolve_recording_period(recording_start_time)

        return RecordingTask(
            title=self.title,
            recording_period=recording_period,
            base_dir=self.output_dir,
            audio_format=self.audio_format,
        )

    def resolve_recording_period(self, recording_start_time: DateTime) -> TimePeriod:
        # Get prev recording period based on cron expression (as we may be within the prev recording period)
        prev_start_time: DateTime = croniter(
            self.cron_expression, start_time=recording_start_time
        ).get_prev(datetime)

        prev_end_time: DateTime = prev_start_time + self.duration.as_timedelta()

        # Check if we are still within the prev recording period
        if recording_start_time < prev_end_time:
            # If recording has been started before the end of the previous recording period, we are still within the previous recording period
            logger.debug(
                f"Schedule '{self.title}': Recording has been started during previous recording period"
            )
            return TimePeriod(
                start=prev_start_time,
                end=prev_end_time,
            )
        else:
            # Get next recording period based on cron expression
            next_start_time: DateTime = croniter(
                self.cron_expression, start_time=recording_start_time
            ).get_next(datetime)
            next_end_time: DateTime = next_start_time + self.duration.as_timedelta()

            return TimePeriod(
                start=next_start_time,
                end=next_end_time,
            )
