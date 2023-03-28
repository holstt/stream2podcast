from dataclasses import dataclass
from datetime import time, datetime, timedelta

from pydantic import DirectoryPath


@dataclass(frozen=True)
class RecordingTask:
    title: str
    start_time: datetime
    end_time: datetime
    output_dir: DirectoryPath

    @property
    def duration(self) -> timedelta:
        return self.end_time - self.start_time


@dataclass(frozen=True)
class RecordingSchedule:
    """A recording schedule defines a period of time in a given day when a recording should be made.

    Args:
        title (str): The title of the schedule.
        start_timeofday (time): The start time of day for the recording period in UTC.
        end_timeofday (time): The end time of day for the recording period in UTC.
    """

    title: str
    start_timeofday: time
    end_timeofday: time
    output_dir: DirectoryPath

    def __post__init__(
        self,
    ):
        if not self.title:
            raise ValueError("Name must not be empty")

        # Ensure start_time is before end_time
        if self.start_timeofday > self.end_timeofday:
            raise ValueError(
                f"Start time {self.start_timeofday} must be before end time {self.end_timeofday}"
            )

    def get_next_recording_task(self, current_time: datetime) -> RecordingTask:
        """Get the next recording task for this schedule.

        Args:
            current_time (datetime): The current time.

        Returns:
            RecordingTask: The next recording task for this schedule.
        """

        start_time: datetime = self.find_next_start_time(current_time)

        # End time date is whatever date we decided for start time above.
        end_time = datetime.combine(start_time.date(), self.end_timeofday)

        return RecordingTask(self.title, start_time, end_time, self.output_dir)

    def find_next_start_time(self, current_time: datetime) -> datetime:
        # Start time is later today, use today's date
        if self.start_timeofday > current_time.time():
            return datetime.combine(current_time.date(), self.start_timeofday)
        # Start time is not later today, but end time is i.e. we should be recording now, use current time
        elif self.end_timeofday > current_time.time():
            return current_time
        # Both start time and end time was earlier today. It's too late to record today, use tomorrow's date
        else:
            return datetime.combine(
                current_time.date() + timedelta(days=1), self.start_timeofday
            )
