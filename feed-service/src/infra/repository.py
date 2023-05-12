# ignore type errors due to no type stubs for feedgen
# pyright: basic
import logging
import os
import re
from abc import ABC, abstractmethod
from datetime import datetime, timezone  # type: ignore
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import yaml
from pydantic import HttpUrl
from slugify import slugify

from src.infra.podcast_file_utils import PodcastFileNameParser, PodcastFileReader
from src.models import Podcast, PodcastEpisode, PodcastMetadata, ValidUrl

logger = logging.getLogger(__name__)


class PodcastLoadError(Exception):
    pass


# TODO: Use base PodcastRepository
# class PodcastRepository(ABC):
#     @abstractmethod
#     def get(self, id: str) -> Podcast:
#         pass

#     @abstractmethod
#     def update_feed(feed):
#         pass


# TODO: Not resp. for url creation, move further up
def create_podcast_url(podcast_title: str, base_url: ValidUrl) -> ValidUrl:
    return ValidUrl(
        # Sluggify to make it url safe
        # Add / for directory
        urljoin(base_url, (slugify(podcast_title) + "/"))
    )


# Reposistory for loading podcasts from the local file system
class LocalPodcastRepository:
    def __init__(self, base_dir: Path, base_url: ValidUrl):
        super().__init__()
        self._base_dir = base_dir
        # XXX: Ctor injection
        self._parser = PodcastFileNameParser()
        self._file_reader = PodcastFileReader()
        self._base_url = base_url

    # Raise exception if no access to the base directory
    # Call at startup to fail fast
    def assert_access(self):
        if not os.access(self._base_dir, os.R_OK | os.W_OK | os.X_OK):
            raise PodcastLoadError(
                f"Unable to access podcast directory: {self._base_dir}"
            )

    # Returns podcast from a given directory
    def get(self, podcast_dir: Path) -> Podcast:
        logger.debug(f"Loading podcast from directory: {podcast_dir}")

        self._assert_dir_exists(podcast_dir)

        # Get podcast metadata
        metadata_yml = self._file_reader.read_metadata(podcast_dir)
        metadata = PodcastMetadata(**metadata_yml)

        # Generate url from podcast title
        podcast_url = create_podcast_url(
            metadata.title, self._base_url
        )  # TODO: Not resp. for url creation, move further up

        # Load episode data from file names in podcast directory
        episodes: list[PodcastEpisode] = []
        for file_entry in self._file_reader.read_episode_files(podcast_dir):
            episode = self._parser.parse_episode(file_entry, podcast_url)
            episodes.append(episode)

        podcast = Podcast(
            title=metadata.title,
            episodes=episodes,
            feed_url=podcast_url,
            description=metadata.description,
            image_url=metadata.image_url,
        )

        logger.debug(
            f"Podcast '{podcast.title}' with {len(podcast)} episode(s) loaded from directory: {podcast_dir}"
        )

        return podcast

    # Raises exception if given directory does not exist
    def _assert_dir_exists(self, podcast_dir: Path):
        if not os.path.isdir(podcast_dir):
            raise PodcastLoadError(f"Directory does not exist: {podcast_dir}")

    # def update_feed(feed: str):
    #     pass
