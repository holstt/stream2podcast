from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import validators  # type: ignore
from pydantic import BaseModel, Field, validator  # type: ignore
from typing_extensions import override


@dataclass(frozen=True)
class PodcastUpdatedEvent:
    episode_id: Path


class ValidUrl(str):
    @override
    def __new__(cls, value: str):
        if not validators.url(value):  # type: ignore
            raise ValueError(f"Invalid url: {value}")
        return super().__new__(cls, value)


@dataclass(frozen=True)
class PodcastEpisode:
    date: datetime
    title: str
    file_size_bytes: int  # Size of the episode file in bytes
    uuid: str  # Unique id for the episode
    file_name: str  # Name of the episode file

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
    file_name: str  # Name of the podcast file

    # Optional
    description: Optional[str] = None
    image_url: Optional[ValidUrl] = None

    def __len__(self):
        return len(self.episodes)

    def __post_init__(self):
        if not self.title:
            raise ValueError(f"Title cannot be empty")


# XXX: Currently DTO for infra. Use in Podcast model?
class PodcastMetadata(BaseModel):
    title: str

    # Optional
    description: Optional[str] = None
    image_url: Optional[ValidUrl] = None

    @validator("image_url", pre=True)
    def validate_image_url(cls, value: str) -> ValidUrl:
        return ValidUrl(value)
