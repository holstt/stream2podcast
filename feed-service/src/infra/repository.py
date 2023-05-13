import logging
from pathlib import Path
from urllib.parse import urljoin

from slugify import slugify

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


# TODO: Not resp. for url creation, move to infra
def create_podcast_url(podcast_title: str, base_url: ValidUrl) -> ValidUrl:
    return ValidUrl(
        # Sluggify to make it url safe
        # Add / for directory
        urljoin(base_url, (slugify(podcast_title) + "/"))
    )


# Reposistory for loading podcasts from the local file system
# Adapts file system representation to the podcast domain model
class FileSystemPodcastRepository:
    def __init__(
        self,
        base_dir: Path,
        base_url: ValidUrl,
        parser: PodcastFileNameParser,
        file_reader: PodcastFileService,
    ):
        super().__init__()
        self._base_dir = base_dir  # TODO: Use base dir
        # XXX: Ctor injection
        self._parser = parser
        self._file_reader = file_reader
        self._base_url = base_url

    # Returns all podcasts from the base directory
    def get_all(self):
        logger.debug(f"Loading all podcasts")
        for podcast_dir in self._file_reader.read_podcast_dirs():
            yield self.get(podcast_id=podcast_dir.name)

    # Returns podcast from a given directory
    def get(self, podcast_id: str) -> Podcast:
        logger.debug(f"Loading podcast: {podcast_id}")
        # Resolve path to podcast directory
        podcast_dir = self._base_dir / podcast_id

        # Get podcast metadata
        metadata_yml = self._file_reader.read_metadata(podcast_dir)
        metadata = PodcastMetadata(**metadata_yml)

        # Generate url from podcast title
        podcast_url = create_podcast_url(
            metadata.title, self._base_url
        )  # TODO: Not resp. for url creation, move to infra

        # Load episode data from file names in podcast directory
        episodes: list[PodcastEpisode] = []
        for file_entry in self._file_reader.read_episode_files(podcast_dir):
            episode = self._parser.parse_episode_file(file_entry, podcast_url)
            episodes.append(episode)

        podcast = Podcast(
            title=metadata.title,
            episodes=episodes,
            feed_url=podcast_url,
            description=metadata.description,
            image_url=metadata.image_url,
        )

        logger.debug(f"Podcast '{podcast.title}' with {len(podcast)} episode(s) loaded")

        return podcast

    def save_feed(self, feed: bytes, podcast_title: str) -> Path:
        return self._file_reader.write_feed(feed, podcast_title)
