from pathlib import Path
from pydantic import HttpUrl
import logging
import src.feed_loader as feed_loader
import src.feed_generator as feed_generator
from pathlib import Path
import os
from pydantic import HttpUrl
import src.feed_usecase as feed_usecase


logger = logging.getLogger(__name__)

# Default name for podcast feed file
FEED_FILE_NAME = "feed.rss"


def iter_dirs(base_dir: Path):
    for dir in os.scandir(base_dir):
        if dir.is_dir():
            yield dir


# Updates podcast feed files for all podcasts located in the given base directory
def write_podcast_feeds(base_dir: Path, base_url: HttpUrl):
    logger.info(
        f"Updating podcast feeds for all podcasts in '{base_dir}' using base url '{base_url}'"
    )

    # Get podcast feed for all podcasts
    for podcast_dir in iter_dirs(base_dir):
        podcast_feed: bytes = generate_podcast_feed(
            Path(podcast_dir.path),
            base_url,
        )
        # Save podcast feed to file
        podcast_feed_file = Path(podcast_dir.path) / FEED_FILE_NAME
        with open(podcast_feed_file, "wb") as f:
            f.write(podcast_feed)

    logger.info(f"Updated podcast feeds for all podcasts in {base_dir}")


# Get podcast feed in bytes for a single podcast
def generate_podcast_feed(podcast_dir: Path, base_url: HttpUrl) -> bytes:
    podcast = feed_loader.load_podcast(podcast_dir, base_url)
    return feed_generator.generate(podcast)
