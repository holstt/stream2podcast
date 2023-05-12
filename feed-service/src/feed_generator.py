# switch to basic due to no type stubs for feedgen
# pyright: basic
import logging

from feedgen import feed

from src.models import Podcast

logger = logging.getLogger(__name__)


# Generate a XML podcast feed for a podcast
def generate(podcast: Podcast) -> bytes:
    logger.debug(f"Generating podcast feed for podcast: {podcast.title}")

    fg = feed.FeedGenerator()

    # fg.author({"name": "John Doe", "email": "john@example.com"})  # TODO: From metadata

    # Add general podcast info
    fg.title(podcast.title)
    fg.link(href=podcast.feed_url, rel="self")
    # fg.subtitle("Feed subtitle")  # TODO: From metadata

    # Set optional fields
    fg.description(podcast.description) if podcast.description else fg.description(
        podcast.title  # Must have description, so if none provided, use title
    )
    fg.image(podcast.image_url) if podcast.image_url else None

    # fg.id(podcast.url)

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
    # rssfeed: bytes = fg.atom_str(pretty=True)
    rssfeed: bytes = fg.rss_str(pretty=True)
    logger.debug(f"Podcast feed generation completed for: {podcast.title}")
    return rssfeed
