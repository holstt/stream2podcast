# switch to basic due to no type stubs for feedgen
# pyright: basic
import logging
from urllib.parse import urljoin

from feedgen import feed
from feedgen.entry import FeedEntry

from src.domain.models import Podcast, PodcastEpisode, ValidUrl

logger = logging.getLogger(__name__)


class UrlGenerator:
    def __init__(self, base_url: ValidUrl) -> None:
        self._base_url = base_url

    def generate_podcast_url(self, podcast_file_name: str) -> ValidUrl:
        return ValidUrl(
            # Add / for directory
            urljoin(self._base_url, podcast_file_name + "/")
        )

    def generate_episode_url(
        self, podcast_url: ValidUrl, episode_file_name: str
    ) -> ValidUrl:
        return ValidUrl(urljoin(podcast_url, episode_file_name))


# Converts a podcast domain model to an RSS feed
class RssFeedAdapter:
    def __init__(self, url_generator: UrlGenerator) -> None:
        super().__init__()
        self._url_generator = url_generator

    # Generates a rss podcast feed from the given podcast
    # NB: Returned as bytes
    def generate_feed(self, podcast: Podcast) -> bytes:
        logger.debug(f"Generating podcast feed for podcast: {podcast.title}")

        rss_feed = feed.FeedGenerator()

        # fg.author({"name": "John Doe", "email": "john@example.com"})  # TODO: From metadata

        # Add general podcast info
        rss_feed.title(podcast.title)

        podcast_url = self._url_generator.generate_podcast_url(podcast.file_name)
        rss_feed.link(href=podcast_url, rel="self")
        # fg.subtitle("Feed subtitle")  # TODO: From metadata

        # Set optional fields
        rss_feed.description(
            podcast.description
        ) if podcast.description else rss_feed.description(
            podcast.title  # Must have description, so if none provided, use title
        )
        rss_feed.image(podcast.image_url) if podcast.image_url else None

        # fg.id(podcast.url)

        # Add entry for each episode
        for episode in podcast.episodes:
            episode_media_url = self._url_generator.generate_episode_url(
                podcast_url, episode.file_name
            )
            feed_entry = self._create_entry(episode, episode_media_url)
            rss_feed.add_entry(feed_entry)

        # Generate the rss feed.
        # rssfeed: bytes = fg.atom_str(pretty=True)
        rssfeed: bytes = rss_feed.rss_str(pretty=True)
        logger.debug(f"Podcast feed generation completed for: {podcast.title}")
        return rssfeed

    def _create_entry(
        self, episode: PodcastEpisode, episode_media_url: ValidUrl
    ) -> FeedEntry:
        feed_entry = FeedEntry()
        feed_entry.title(episode.title)
        # Webpage associated with episode. Let's just use the media url
        feed_entry.link(href=episode_media_url)

        # Url to media file
        feed_entry.enclosure(
            url=episode_media_url,
            length=str(episode.file_size_bytes),
            type="audio/mpeg",
        )

        # guid should be unique (not just for this podcast), let's use the uuid of the episode
        # permalink=True, permanent link indicates guid will not change
        feed_entry.guid(episode.uuid, permalink=True)

        feed_entry.pubDate(episode.date)
        return feed_entry
