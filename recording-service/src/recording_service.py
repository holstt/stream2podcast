import asyncio
import logging
from typing import Any

from pendulum import DateTime, Duration, Period, Time  # type: ignore

from src import audio_storage, utils
from src.audio_storage import AudioStorageAdapter
from src.audio_stream import HttpAudioStreamAdapter
from src.models import RecordingSchedule, RecordingTask, ValidUrl

logger = logging.getLogger(__name__)


class RecordAudioService:
    def __init__(
        self,
        audio_stream_adapter: HttpAudioStreamAdapter,
        audio_storage_adapter: audio_storage.AudioStorageAdapter,
        stream_url: ValidUrl,
        time_provider: utils.TimeProvider,
    ) -> None:
        super().__init__()
        self._audio_storage_adapter = audio_storage_adapter
        self._audio_stream_adapter = audio_stream_adapter
        self._stream_url = stream_url
        self._time_provider = time_provider

    # Records audio for a given task
    async def record_audio_task(self, task: RecordingTask, metadata: dict[str, Any]):
        current_time = self._time_provider.get_current_time()

        # Account for task being in the future
        await self.wait_until_start_if_in_future(task, current_time)

        # Account for starting in between the recording period
        duration_left = self.get_duration_left(task, current_time)

        # Ensure output directory exist with metadata
        audio_storage.ensure_dir_with_metadata(task.file_path.parent, metadata=metadata)

        logger.info(
            f"Starting recording for task: {task.id}. Duration: {duration_left}. Writing to path: {task.file_path}"
        )

        # XXX: Consider moving countdown timer here instead of hidden in adapter

        # Get audio data iterator from the live stream
        audio_data_iterator = self._audio_stream_adapter.get_audio_data(
            self._stream_url,
            utils.CountdownTimer(duration_left, time_provider=self._time_provider),
            stream_name=task.title,
        )

        await self._audio_storage_adapter.save(audio_data_iterator, task.file_path)
        logger.info(f"Recording complete. Saved at: {task}")

    def get_duration_left(self, task: RecordingTask, current_time: DateTime):
        duration_left = task.recording_period.get_time_remaining(current_time)
        # Fail if no duration left.
        if duration_left.in_seconds() <= 0:
            raise ValueError(
                f"Task '{task.title}': Recording start time {task.recording_period.start} is later than current time {current_time}"
            )
        else:
            logger.debug(
                f"Task '{task.title}': Duration reduced from {task.recording_period.duration} to {duration_left} (task start time: {task.recording_period.start.time()}, actual start time: {current_time.time()}))"
            )

        return duration_left

    # Waits until the start time of the task if it is in the future
    async def wait_until_start_if_in_future(
        self, task: RecordingTask, current_time: DateTime
    ):
        until_start = task.recording_period.get_time_until_start(current_time)
        if until_start.in_seconds() > 0:
            logger.info(
                f"Task '{task.title}': Waiting until start time {task.recording_period.start} (in {until_start})"
            )
            await asyncio.sleep(until_start.in_seconds())
