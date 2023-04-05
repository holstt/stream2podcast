from dataclasses import dataclass
from datetime import datetime
from pydantic import HttpUrl


@dataclass(frozen=True)
class PodcastEpisode:
    date: datetime
    title: str
    media_url: HttpUrl  # Full url to the episode file
    file_size_bytes: int  # Size of the episode file in bytes
    uuid: str  # Unique id for the episode

    def __post_init__(self):
        if not self.title:
            raise ValueError(f"Title cannot be empty")
        if not self.uuid:
            raise ValueError(f"UUID cannot be empty")
        if self.file_size_bytes <= 0:
            raise ValueError(f"File size cannot be 0 or negative")


@dataclass(frozen=True)
class Podcast:
    title: str
    episodes: list[PodcastEpisode]
    url: HttpUrl  # Full url to the podcast feed

    def __len__(self):
        return len(self.episodes)

    def __post_init__(self):
        if not self.title:
            raise ValueError(f"Title cannot be empty")
