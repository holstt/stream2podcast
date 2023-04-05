import logging
from src import utils
from src import config
from src.config import AppConfig
import src.feed_usecase as feed_usecase

logger = logging.getLogger(__name__)


def main(app_config: AppConfig):
    feed_usecase.write_podcast_feeds(
        app_config.base_dir,
        app_config.base_url,
    )


if __name__ == "__main__":
    # utils.setup_logging()
    utils.setup_logging(logging.DEBUG)
    try:
        config_file_path = utils.read_config_path()
        app_config = config.from_yml(config_file_path)
        main(app_config)
    except Exception as e:
        logger.exception(f"Unhandled exception occurred: {e}")
        raise e
