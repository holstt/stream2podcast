import logging
import os
import re
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import yaml
from pydantic import HttpUrl
from slugify import slugify

from src.models import Podcast, PodcastEpisode, ValidUrl


class PodcastParserError(Exception):
    pass


# Parses information from podcast files and directories
class PodcastFileNameParser:
    # Returns a PodcastEpisode object based on the episode file information
    def parse_episode(
        self, file_entry: os.DirEntry[str], podcast_url: ValidUrl  # TODO: Remove url
    ) -> PodcastEpisode:
        # Pattern example: 2023-04-03--1200-1400--episode-title--ee1ad7c6-95bf-4116-a1f8-060053e80a73.mp3
        EPISODE_FILENAME_PATTERN = r"^(?P<date>\d{4}-\d{2}-\d{2})--(?P<start_time>\d{4})-(?P<end_time>\d{4})--(?P<title>.*?)--(?P<uuid>[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\.(?P<file_ext>mp3|mp4)$"

        # Apply regex pattern to file name
        match = re.match(EPISODE_FILENAME_PATTERN, file_entry.name)

        # If any file name does not follow pattern, abort to avoid incomplete feed
        if not match:
            raise PodcastParserError(
                f"Episode file name {file_entry.name} does not follow the required format: {EPISODE_FILENAME_PATTERN}"
            )

            # Extract data from file name
        date_str = match.group("date")
        uuid_str = match.group("uuid")

        date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)

        episode_media_url = ValidUrl(
            urljoin(podcast_url, file_entry.name),
        )

        # Get size of file in bytes
        file_size = file_entry.stat().st_size

        episode = PodcastEpisode(
            date=date,
            title=date.strftime("%Y-%m-%d"),
            media_url=episode_media_url,
            file_size_bytes=file_size,
            uuid=uuid_str,
        )

        return episode

    def parse_title(self, podcast_dir_name: str):
        return slugify(podcast_dir_name, separator=" ").title()


class PodcastFileReader:
    VALID_EPISODE_FILE_EXTENSIONS = (".mp3", ".mp4")  # TODO: From config
    METADATA_FILE_NAME = "metadata.yml"  # TODO: From config

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
