import asyncio
import logging
import time
from pathlib import Path
from turtle import update
from typing import Any, Callable

from typing_extensions import override
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

import src.feed_usecase as feed_usecase
from src import config, utils
from src.config import AppConfig

logger = logging.getLogger(__name__)


class FileChangedEventHandler(FileSystemEventHandler):
    # Callable takes the path of the file that triggered the event
    def __init__(self, callback: Callable[[Path], None]) -> None:
        super().__init__()
        self.callback = callback
        # XXX: Ignore multiple events for the same file within the debounce time
        # self.debounce_seconds = 5
        self.pending_events: dict[float, str] = {}

    # Triggers on any kind of file change
    def on_any_event(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return

        logger.info(f"{event.event_type} - {event.src_path}")
        self.callback(Path(event.src_path))


# XXX: Updates all feeds on any file change atm.
def update_feeds(file_path: Path):
    # Ignore updates to rss feed files to avoid infinite loop
    if file_path.name == feed_usecase.FEED_FILE_NAME:
        return

    logger.info(f"A file changed: {file_path}, updating all feeds")
    feed_usecase.write_podcast_feeds(
        app_config.base_dir,
        app_config.base_url,
    )
    logger.info("Finished updating all feeds")


async def main(app_config: AppConfig):
    event_handler = FileChangedEventHandler(update_feeds)
    observer = Observer()
    logger.info(f"Monitoring directory for file changes: {app_config.base_dir}")
    observer.schedule(event_handler, path=app_config.base_dir, recursive=True)

    # Start monitoring
    observer.start()

    try:
        loop = asyncio.get_event_loop()
        while True:
            await asyncio.sleep(0)

    finally:
        observer.stop()
        observer.join()


if __name__ == "__main__":
    # utils.setup_logging()
    utils.setup_logging(logging.DEBUG)
    try:
        config_file_path = utils.read_config_path()
        app_config = config.from_yaml(config_file_path)
        asyncio.run(main(app_config))
    except Exception as e:
        logger.exception(f"Unhandled exception occurred: {e}")
        raise e
