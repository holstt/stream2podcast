import logging
from pathlib import Path

from src.domain.models import Podcast
from src.infra.repository import FileSystemPodcastRepository
from src.infra.rss_feed_adapter import RssFeedAdapter

logger = logging.getLogger(__name__)


class GeneratePodcastFeedUseCase:
    def __init__(
        self, repo: FileSystemPodcastRepository, generator: RssFeedAdapter
    ) -> None:
        super().__init__()
        self._repo = repo
        self.generator = generator

    # Generates podcast feed .rss files for ALL podcasts located in the given base directory
    def generate_feeds(self) -> list[Path]:
        logger.info(f"Updating podcast feeds for all podcasts")

        feed_paths: list[Path] = []

        # Get podcast feed for all podcasts
        for podcast in self._repo.get_all():
            feed_path = self._generate_and_save_feed(podcast)
            feed_paths.append(feed_path)

        logger.info(f"Updated podcast feeds for all podcasts")
        return feed_paths

    # Generates podcast feed .rss file for the podcast located in the given directory
    def generate_feed(self, podcast_id: str) -> Path:
        podcast = self._repo.get(podcast_id)
        feed_path = self._generate_and_save_feed(podcast)
        return feed_path

    def _generate_and_save_feed(self, podcast: Podcast):
        logger.info(f"Generating podcast feed for podcast '{podcast.title}'")
        feed = self.generator.generate_feed(podcast)
        # Save podcast feed to file
        feed_file_path = self._repo.save_feed(feed, podcast.title)
        logger.info(f"Podcast feed generated: '{feed_file_path}'")
        return feed_file_path
