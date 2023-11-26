import logging
import os
from pathlib import Path
from threading import Lock
from typing import Any

import yaml
from slugify import slugify

logger = logging.getLogger(__name__)

# Adapter for local podcast file storage

# Shared lock for writing to feed files
lock = Lock()


class PodcastFileServiceError(Exception):
    pass


class PodcastFileService:
    # TODO: Move to config
    FEED_FILE_NAME = "feed.rss"
    METADATA_FILE_NAME = "metadata.yml"
    VALID_EPISODE_FILE_EXTENSIONS = (".mp3", ".mp4")

    def __init__(self, base_dir: Path) -> None:
        super().__init__()
        self._base_dir = base_dir
        logger.info(f"Using podcast base directory: {self._base_dir}")

    def read_podcast_dirs(self):
        for dir_entry in os.scandir(self._base_dir):
            if dir_entry.is_dir():
                yield dir_entry

    # Returns an iterator over all episode files in a given podcast directory
    def read_episode_files(self, podcast_dir: Path):
        for dir_entry in os.scandir(podcast_dir):
            if dir_entry.is_file() and dir_entry.name.endswith(
                self.VALID_EPISODE_FILE_EXTENSIONS
            ):
                yield dir_entry

    # Reads the metadata file stored in the given podcast directory
    def read_metadata(self, podcast_dir: Path):
        meta_file = Path(podcast_dir / self.METADATA_FILE_NAME)
        with open(meta_file, "r", encoding="utf-8") as f:
            metadata: dict[str, Any] = yaml.safe_load(f)
        return metadata

    def write_feed(self, feed: bytes, podcast_title: str) -> Path:
        # Convert title to podcast dir
        podcast_dir = self._base_dir / slugify(
            podcast_title
        )  # TODO: Use identifier instead of relying on title slug
        feed_file_path = podcast_dir / self.FEED_FILE_NAME

        with lock:
            with open(feed_file_path, "wb") as f:
                f.write(feed)
        return feed_file_path

    # Raise exception if no access to the base directory
    # Call at startup to fail fast
    def assert_access(self):
        logger.info(f"Checking access to podcast base directory: {self._base_dir}")
        if not os.access(self._base_dir, os.R_OK | os.W_OK | os.X_OK):
            raise PodcastFileServiceError(
                f"Unable to access the base directory for podcasts: {self._base_dir}"
            )

    # XXX: Not used atm
    # Raises exception if given directory does not exist
    def _assert_podcast_dir_exists(self, podcast_dir: Path) -> None:
        if not os.path.isdir(podcast_dir):
            raise PodcastFileServiceError(
                f"Podcast directory does not exist: {podcast_dir}"
            )
