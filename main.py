import logging
import asyncio
from src import utils
from src.config_parser import AppConfig
from src.recorder_service import start_recording_loop
import src.config_parser as config_parser

logger = logging.getLogger(__name__)


async def main(config: AppConfig):
    await start_recording_loop(config.stream_url, config.recording_schedules)


if __name__ == "__main__":
    utils.setup_logging()
    try:
        config_file_path = utils.get_args_config_path()
        config = config_parser.parse(config_file_path)

        asyncio.run(main(config))
    except Exception as e:
        logger.exception(f"Unhandled exception occurred: {e}")
        raise e
