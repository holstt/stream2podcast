import logging
from datetime import timedelta
from typing import NamedTuple

from src.application.generate_podcast_feed_usecase import GeneratePodcastFeedUseCase
from src.application.podcast_updated_event_handler import PodcastUpdatedEventHandler
from src.config import AppConfig
from src.infra.file_changed_handler import FileChangedEventHandler
from src.infra.file_changed_monitor import FileChangedMonitor
from src.infra.file_parser import PodcastFileNameParser
from src.infra.file_reader import PodcastFileService
from src.infra.repository import FileSystemPodcastRepository
from src.infra.rss_feed_adapter import RssFeedAdapter, UrlGenerator

logger = logging.getLogger(__name__)


class Dependencies(NamedTuple):
    repo: FileSystemPodcastRepository
    generator: RssFeedAdapter
    usecase: GeneratePodcastFeedUseCase
    feed_updated_handler: PodcastUpdatedEventHandler
    file_changed_handler: FileChangedEventHandler
    directory_monitor: FileChangedMonitor


# Resolve deps
def resolve(app_config: AppConfig):
    parser = PodcastFileNameParser()
    file_service = PodcastFileService(app_config.base_dir)

    repo = FileSystemPodcastRepository(
        app_config.base_dir,
        parser,
        file_service,
    )

    url_generator = UrlGenerator(app_config.base_url)
    rss_generator = RssFeedAdapter(url_generator)

    usecase = GeneratePodcastFeedUseCase(repo, rss_generator)
    feed_updated_handler = PodcastUpdatedEventHandler(usecase)

    # On a file change in the feed storage, require 5 minutes without further change to the file before triggering the callback that updates the corresponding podcast feed. This ensures that the podcast feed is not updated before a recording is finished.
    debounce_time = timedelta(minutes=5)  # TODO: From config
    file_changed_handler = FileChangedEventHandler(
        debounce_time,
        callback=lambda podcast_update_event: feed_updated_handler.handle(
            podcast_update_event
        ),
    )
    directory_monitor = FileChangedMonitor(app_config.base_dir, file_changed_handler)
    return Dependencies(
        repo,
        rss_generator,
        usecase,
        feed_updated_handler,
        file_changed_handler,
        directory_monitor,
    )
