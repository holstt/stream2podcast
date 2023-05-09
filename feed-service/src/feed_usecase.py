import logging
import os
from pathlib import Path
from threading import Lock

from pydantic import HttpUrl

import src.feed_generator as feed_generator
import src.feed_loader as feed_loader
import src.feed_usecase as feed_usecase

logger = logging.getLogger(__name__)

# Shared lock for writing to feed files
lock = Lock()

# Default name for podcast feed file
FEED_FILE_NAME = "feed.rss"


# Updates podcast feed .rss files for ALL podcasts located in the given base directory
def update_podcast_feeds(base_dir: Path, base_url: HttpUrl):
    logger.info(
        f"Updating podcast feeds for all podcasts in '{base_dir}' using base url '{base_url}'"
    )

    # Get podcast feed for all podcasts
    for podcast_dir in _iter_dirs(base_dir):
        update_podcast_feed(Path(podcast_dir.path), base_url)

    logger.info(f"Updated podcast feeds for all podcasts in {base_dir}")


# Updates podcast feed .rss file for the podcast located in the given directory
def update_podcast_feed(podcast_dir: Path, base_url: HttpUrl):
    logger.info(f"Updating podcast feed for podcast in '{podcast_dir}'")
    podcast_feed: bytes = _generate_podcast_feed(
        podcast_dir,
        base_url,
    )
    # Save podcast feed to file
    podcast_feed_file = podcast_dir / FEED_FILE_NAME
    with lock:
        with open(podcast_feed_file, "wb") as f:
            f.write(podcast_feed)

    logger.info(f"Podcast feed has been updated for podcast in '{podcast_dir}'")


# Generates a podcast feed based on the content of the given podcast directory
# NB: Returns bytes
def _generate_podcast_feed(podcast_dir: Path, base_url: HttpUrl) -> bytes:
    podcast = feed_loader.load_podcast(podcast_dir, base_url)
    return feed_generator.generate(podcast)


def _iter_dirs(base_dir: Path):
    for dir in os.scandir(base_dir):
        if dir.is_dir():
            yield dir
