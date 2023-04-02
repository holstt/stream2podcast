import logging
import asyncio

from pydantic import HttpUrl
from src import utils
from src.config_parser import AppConfig
from src.record_audio_usecase import start_recording_loop
import src.config_parser as config_parser
from src.record_audio_client import StreamRecorder, HSLStreamRecorder, ICYStreamRecorder

logger = logging.getLogger(__name__)


def get_recorder(stream_url: HttpUrl) -> StreamRecorder:
    if stream_url.endswith(".m3u8"):
        logger.info("Using HSL stream recorder")
        return HSLStreamRecorder(stream_url)
    else:
        logger.info("Using ICY stream recorder")
        return ICYStreamRecorder(stream_url)


async def main(config: AppConfig):
    # Resolve recorder based on url # XXX: As factory -> Move to usecase?
    await start_recording_loop(
        config.recording_schedules, get_recorder(config.stream_url)
    )


if __name__ == "__main__":
    # utils.setup_logging()
    utils.setup_logging(logging.DEBUG)
    try:
        config_file_path = utils.read_config_path()
        config = config_parser.parse(config_file_path)

        asyncio.run(main(config))
    except Exception as e:
        logger.exception(f"Unhandled exception occurred: {e}")
        raise e
