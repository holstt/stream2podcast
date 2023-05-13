import logging

from src.application.generate_podcast_feed_usecase import GeneratePodcastFeedUseCase
from src.domain.models import PodcastUpdatedEvent

logger = logging.getLogger(__name__)


class PodcastUpdatedEventHandler:
    def __init__(self, usecase: GeneratePodcastFeedUseCase) -> None:
        super().__init__()
        self.usecase = usecase

    def handle(self, event: PodcastUpdatedEvent):
        logger.debug(f"Podcast updated event received for podcast '{event.episode_id}'")
        podcast_id = event.episode_id.parent.name
        self.usecase.generate_feed(podcast_id)
