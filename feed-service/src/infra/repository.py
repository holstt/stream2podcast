import logging
from pathlib import Path

from src.domain.models import Podcast, PodcastEpisode, PodcastMetadata, ValidUrl
from src.infra.file_parser import PodcastFileNameParser
from src.infra.file_reader import PodcastFileService

logger = logging.getLogger(__name__)


class RepositoryError(Exception):
    pass


# TODO: Use base PodcastRepository in domain layer
# class PodcastRepository(ABC):
#     @abstractmethod
#     def get(self, id: str) -> Podcast:
#         pass

#     @abstractmethod
#     def update_feed(feed):
#         pass


# Reposistory for loading podcasts from the local file system
# Adapts file system representation to the podcast domain model
class FileSystemPodcastRepository:
    def __init__(
        self,
        base_dir: Path,
        parser: PodcastFileNameParser,
        file_service: PodcastFileService,
    ):
        super().__init__()
        self._base_dir = base_dir
        self._parser = parser
        self._file_service = file_service

    # Returns all podcasts from the base directory
    def get_all(self):
        logger.debug(f"Loading all podcasts")
        for podcast_dir in self._file_service.read_podcast_dirs():
            yield self.get(podcast_id=podcast_dir.name)

    # Returns podcast from a given directory
    def get(self, podcast_id: str) -> Podcast:
        logger.debug(f"Loading podcast: {podcast_id}")
        # Resolve path to podcast directory
        podcast_dir = self._base_dir / podcast_id

        # Get podcast metadata
        metadata_yml = self._file_service.read_metadata(podcast_dir)
        metadata = PodcastMetadata(**metadata_yml)

        # Load episode data from file names in podcast directory
        episodes: list[PodcastEpisode] = []
        for file_entry in self._file_service.read_episode_files(podcast_dir):
            episode = self._parser.parse_episode_file(file_entry)
            episodes.append(episode)

        podcast = Podcast(
            title=metadata.title,
            episodes=episodes,
            description=metadata.description,
            image_url=metadata.image_url,
            file_name=podcast_dir.name,
        )

        logger.debug(f"Podcast '{podcast.title}' with {len(podcast)} episode(s) loaded")

        return podcast

    def save_feed(self, feed: bytes, podcast_title: str) -> Path:
        return self._file_service.write_feed(feed, podcast_title)
