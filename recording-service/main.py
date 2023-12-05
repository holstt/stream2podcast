import asyncio
import logging
from ctypes import util

from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore
from pydantic import HttpUrl

import src.config
from src import utils
from src.audio_storage import AudioStorageAdapter
from src.audio_stream import (
    HlsAudioStreamAdapter,
    HttpAudioStreamAdapter,
    HttpStreamClient,
)
from src.config import AppConfig
from src.models import ValidUrl
from src.recording_service import RecordAudioService
from src.scheduler_service import RecordingSchedulerService

logger = logging.getLogger(__name__)

CHUNK_SIZE = (
    1 * 1024
)  # Read/write x KB at a time # XXX: Experiment with this wrt performance and memory usage


def resolve_dependencies(stream_url: ValidUrl):
    http_stream_client = HttpStreamClient(CHUNK_SIZE)
    if stream_url.endswith(".m3u8"):
        audio_format: str = "mp4"
        stream_adapter = HlsAudioStreamAdapter(http_stream_client)
    else:
        audio_format: str = "mp3"
        stream_adapter = HttpAudioStreamAdapter(http_stream_client)

    audio_service = RecordAudioService(
        stream_adapter,
        AudioStorageAdapter(),
        stream_url,
        utils.TimeProvider(),
    )

    return audio_service, utils.TimeProvider(), audio_format


# Starts the recording scheduler with the given config
def main(config: AppConfig):
    scheduler = RecordingSchedulerService(*resolve_dependencies(config.stream_url))
    [
        scheduler.add_recording_schedule(schedule)
        for schedule in config.recording_schedules
    ]

    scheduler.run()


if __name__ == "__main__":
    # utils.setup_logging()
    utils.setup_logging(logging.DEBUG)
    try:
        config_file_path = utils.read_config_path()
        config = src.config.from_yaml(config_file_path)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        main(config)
        loop.run_forever()
    # Do nothing on keyboard interrupt
    except (KeyboardInterrupt, SystemExit):
        pass
    # Log unhandled exceptions and terminate the program
    except Exception as e:
        logger.exception(f"Unhandled exception occurred: {e}")
        raise e
