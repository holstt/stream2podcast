# switch to basic due to no type stubs for feedgen
# pyright: basic
from feedgen import feed
from src.models import Podcast
import logging

logger = logging.getLogger(__name__)

# Generate a XML podcast feed for a podcast
def generate(podcast: Podcast) -> bytes:
    logger.debug(f"Generating podcast feed for podcast: {podcast.title}")

    fg = feed.FeedGenerator()

    # Add general podcast info
    fg.title(podcast.title)
    fg.subtitle("Feed subtitle")  # TODO: From config
    fg.description("A description of " + podcast.title)  # TODO: From config

    fg.author({"name": "John Doe", "email": "john@example.com"})  # TODO: From config

    fg.link(href=podcast.url, rel="self")

    # Add entry for each episode
    for episode in podcast.episodes:
        fe = fg.add_entry()
        fe.title(episode.title)
        # Webpage associated with episode. Let's just use the media url
        fe.link(href=episode.media_url)

        # Url to media file
        fe.enclosure(
            url=episode.media_url,
            length=str(episode.file_size_bytes),
            type="audio/mpeg",
        )

        # guid should be unique (not just for this podcast), let's use the uuid of the episode
        # permalink=True, permanent link indicates guid will not change
        fe.guid(episode.uuid, permalink=True)

        fe.pubDate(episode.date)

    # Generate the rss feed. Is returned as bytes
    rssfeed: bytes = fg.rss_str(pretty=True)
    logger.debug(f"Podcast feed generation completed for: {podcast.title}")
    return rssfeed
