import os
import re
from datetime import datetime, timezone
from urllib.parse import urljoin

from src.domain.models import PodcastEpisode, ValidUrl


class PodcastParserError(Exception):
    pass


# Maps episode file name -> PodcastEpisode


# Parses information from podcast files and directories
class PodcastFileNameParser:
    # Pattern example: 2023-04-03--1200-1400--episode-title--ee1ad7c6-95bf-4116-a1f8-060053e80a73.mp3
    EPISODE_FILENAME_PATTERN = r"^(?P<date>\d{4}-\d{2}-\d{2})--(?P<start_time>\d{4})-(?P<end_time>\d{4})--(?P<title>.*?)--(?P<uuid>[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\.(?P<file_ext>mp3|mp4)$"

    # Returns a PodcastEpisode object based on the episode file information
    def parse_episode_file(
        self, file_entry: os.DirEntry[str], podcast_url: ValidUrl  # TODO: Remove url
    ) -> PodcastEpisode:
        # Apply regex pattern to file name
        match = re.match(self.EPISODE_FILENAME_PATTERN, file_entry.name)

        # If any file name does not follow pattern, abort to avoid incomplete feed
        if not match:
            raise PodcastParserError(
                f"Episode file name {file_entry.name} does not follow the required format: {self.EPISODE_FILENAME_PATTERN}"
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
