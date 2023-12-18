import logging
from datetime import datetime
from typing import Optional

# import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore
from apscheduler.triggers.cron import CronTrigger  # type: ignore
from pendulum import DateTime, Duration, Time  # type: ignore

from src import utils
from src.models import RecordingSchedule
from src.recording_service import RecordAudioService

logger = logging.getLogger(__name__)


class SchedulerError(Exception):
    pass


# Scheduler service for scheduling recording jobs.
class RecordingSchedulerService:
    def __init__(
        self,
        recording_service: RecordAudioService,
        time_provider: utils.TimeProvider,
        audio_format: str,
    ) -> None:
        super().__init__()
        self._recorder = recording_service
        self._time_provider = time_provider
        self.audio_format = audio_format
        # Create async scheduler for running async tasks
        self.scheduler = AsyncIOScheduler(timezone="UTC")

    def add_recording_schedule(self, recording_schedule: RecordingSchedule):
        current_time = self._time_provider.get_current_time()

        # Check if we should be recording right now, then set next run time to right now
        # Get inital task to run to peek at the recording period
        initial_task = recording_schedule.get_current_or_next_task(current_time)
        is_due = (
            initial_task.recording_period.start <= current_time
            and current_time <= initial_task.recording_period.end
        )

        next_run_time = None
        # If due, schedule a recording task to run immediately
        if is_due:
            # Delay by 5 seconds to allow scheduler to start
            next_run_time = current_time + Duration(seconds=5)
            logger.info(
                f"Scheduler was started during a recording period for '{recording_schedule.title}' and will be run immediately (next run scheduled for now + 5 sec. delay): {next_run_time}"
            )

        self._add_job(recording_schedule, next_run_time)

    # Schedules a recording task to run at the specified time
    def _add_job(
        self,
        recording_schedule: RecordingSchedule,
        next_run_time: Optional[DateTime] = None,
    ):
        try:
            trigger = self._get_trigger(
                recording_schedule.frequency,
                recording_schedule.start_timeofday,
            )

            job = self.scheduler.add_job(
                func=self._execute_recording_task,
                trigger=trigger,
                args=[recording_schedule],
                id=str(recording_schedule.id),
                name=recording_schedule.title,
            )

            # Add next run time to job if specified
            if next_run_time is not None:
                # Convert pendulum DateTime to python datetime as apscheduler doesn't like pendulum DateTime... (AttributeError: 'NoneType' object has no attribute 'convert')
                job.next_run_time = self._pendulum_dt_to_std_dt(next_run_time)

        except ValueError as e:
            raise SchedulerError(
                f"An incorrect value was specified while adding job: {e}"
            ) from e

    # Converts a pendulum DateTime to a python datetime
    def _pendulum_dt_to_std_dt(self, next_run_time: DateTime) -> datetime:
        # datetime_string = next_run_time.to_iso8601_string()
        next_run_time_std_dt = datetime.fromtimestamp(
            next_run_time.timestamp(), tz=next_run_time.timezone  # type: ignore
        )
        return next_run_time_std_dt

    # Gets trigger based on frequency
    def _get_trigger(self, frequency: str, start_time: Time):
        return CronTrigger(
            day_of_week=frequency,
            hour=start_time.hour,
            minute=start_time.minute,
            second=start_time.second,
            timezone="UTC",
        )

    async def _execute_recording_task(self, recording_schedule: RecordingSchedule):
        logger.info(
            f"Executing task for recording schedule: {recording_schedule.title}"
        )

        current_time = self._time_provider.get_current_time()
        task = recording_schedule.get_current_or_next_task(
            recording_start_time=current_time
        )

        try:
            await self._recorder.record_audio_task(task, recording_schedule.metadata)
            logger.info(f"Recording task complete: {task}")

        except Exception as e:
            raise SchedulerError(f"Recording failed: {task}, {e}") from e

    def run(self):
        logger.info(f"Starting scheduler with jobs:")
        self.scheduler.print_jobs()

        self.scheduler.start()  # NB: Non-blocking, caller responsible for keeping process alive
