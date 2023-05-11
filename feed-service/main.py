import asyncio
import logging
from datetime import timedelta
from pathlib import Path

import src.feed_usecase as feed_usecase
from src import config, utils
from src.config import AppConfig
from src.monitor_service import FileChangedEventHandler, FileMonitorService

logger = logging.getLogger(__name__)


def update_feed(feed_file_changed: Path):
    # Ignore any changes to the .rss feed files themselves
    if feed_file_changed.name == feed_usecase.FEED_FILE_NAME:
        return

    # Get name of podcast directory
    podcast_dir = feed_file_changed.parent

    feed_usecase.update_podcast_feed(
        podcast_dir,
        app_config.base_url,
    )


def main(app_config: AppConfig):
    if app_config.should_update_feeds_on_startup:
        feed_usecase.update_podcast_feeds(app_config.base_dir, app_config.base_url)

    # On a file change in the feed storage, require 5 minutes without further change to the file before triggering the callback that updates the corresponding podcast feed. This ensures that the podcast feed is not updated before a recording is finished.
    debounce_time = timedelta(minutes=5)
    event_handler = FileChangedEventHandler(
        debounce_time, callback=lambda file_path: update_feed(file_path)
    )
    directory_monitor = FileMonitorService(app_config.base_dir, event_handler)
    directory_monitor.start()


if __name__ == "__main__":
    utils.setup_logging()
    # utils.setup_logging(logging.DEBUG)
    try:
        config_file_path = utils.read_config_path()
        app_config = config.from_yaml(config_file_path)
        main(app_config)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.exception(f"Unhandled exception occurred: {e}")
        raise e
