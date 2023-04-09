import asyncio
import logging

from pydantic import HttpUrl

import src.config as config
from src import utils
from src.audio_storage import AudioStorageAdapter
from src.audio_stream import (
    HlsAudioStreamAdapter,
    HttpAudioStreamAdapter,
    HttpStreamClient,
)
from src.config import AppConfig
from src.models import ValidUrl
from src.recording_service import start

logger = logging.getLogger(__name__)

CHUNK_SIZE = 1024  # Read 1KB at a time # XXX: Experiment with this wrt performance and memory usage

# resolve dep
def resolve_deps(stream_url: ValidUrl):
    http_stream_client = HttpStreamClient(CHUNK_SIZE)

    if stream_url.endswith(".m3u8"):
        return HlsAudioStreamAdapter(http_stream_client), AudioStorageAdapter("mp4")
    else:
        return HttpAudioStreamAdapter(http_stream_client), AudioStorageAdapter("mp3")


async def main(config: AppConfig):
    await start(
        config.recording_schedules, config.stream_url, *resolve_deps(config.stream_url)
    )


if __name__ == "__main__":
    # utils.setup_logging()
    utils.setup_logging(logging.DEBUG)
    try:
        config_file_path = utils.read_config_path()
        config = config.from_yaml(config_file_path)

        asyncio.run(main(config))
    except Exception as e:
        logger.exception(f"Unhandled exception occurred: {e}")
        raise e
