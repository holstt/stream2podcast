# ignore type errors due to no type stubs for feedgen
# pyright: basic
import logging
import os
import re
from datetime import datetime, timezone  # type: ignore
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import yaml
from pydantic import HttpUrl
from slugify import slugify

from src.models import Podcast, PodcastEpisode

logger = logging.getLogger(__name__)


def to_title(title: str):
    return slugify(title, separator=" ").title()


class PodcastLoadError(Exception):
    pass


# Valid file extensions for episode files
VALID_AUDIO_FILE_ENDINGS = (".mp3", ".mp4")


def iter_episode_files(podcast_directory: Path):
    for f in os.scandir(podcast_directory):
        if f.is_file() and f.name.endswith(VALID_AUDIO_FILE_ENDINGS):
            yield f


# Loads podcast from a given directory
def load_podcast(podcast_directory: Path, base_url: HttpUrl) -> Podcast:
    logger.debug(f"Loading podcast from directory: {podcast_directory}")
    # Ensure directory exists
    if not os.path.isdir(podcast_directory):
        raise PodcastLoadError(f"Directory does not exist: {podcast_directory}")

    # Podcast title is the directory name
    podcast_title = to_title(podcast_directory.name)

    # Generate url from podcast title
    podcast_url = HttpUrl(
        # Add / for directory
        urljoin(base_url, (slugify(podcast_title) + "/")),
        scheme="https",
    )

    # Pattern example: 2023-04-03--1200-1400--episode-title--ee1ad7c6-95bf-4116-a1f8-060053e80a73.mp3
    episode_file_pattern = r"^(?P<date>\d{4}-\d{2}-\d{2})--(?P<start_time>\d{4})-(?P<end_time>\d{4})--(?P<title>.*?)--(?P<uuid>[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\.(?P<file_ext>mp3|mp4)$"

    episodes: list[PodcastEpisode] = []
    for file in iter_episode_files(podcast_directory):
        # Apply regex pattern to file name
        match = re.match(episode_file_pattern, file.name)

        # If any file name does not follow pattern, abort to avoid incomplete feed
        if not match:
            raise PodcastLoadError(
                f"File name {file.name} does not follow the required format: {episode_file_pattern}"
            )

        # Extract data from file name
        date_str = match.group("date")
        uuid_str = match.group("uuid")

        date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)

        episode_media_url = HttpUrl(
            urljoin(podcast_url, file.name),
            scheme="https",
        )

        # Get size of file in bytes
        file_size = file.stat().st_size

        episode = PodcastEpisode(
            date=date,
            title=date.strftime("%Y-%m-%d"),
            media_url=episode_media_url,
            file_size_bytes=file_size,
            uuid=uuid_str,
        )

        episodes.append(episode)

    # Get meta data file # TODO: Validate (see recording-service)
    meta_file = Path(podcast_directory) / "metadata.yml"
    with open(meta_file, "r", encoding="utf-8") as f:
        metadata: dict[str, Any] = yaml.safe_load(f)

    podcast = Podcast(
        title=podcast_title,
        episodes=episodes,
        feed_url=podcast_url,
        description=metadata.get("description"),
        image_url=metadata.get("image_url"),
    )

    logger.debug(
        f"Podcast '{podcast.title}' with {len(podcast)} episode(s) loaded from directory: {podcast_directory}"
    )

    return podcast
