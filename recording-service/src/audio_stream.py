import asyncio
import logging
from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional
from urllib.parse import urljoin

import aiohttp
import m3u8  # type: ignore

from src import utils
from src.models import ValidUrl

logger = logging.getLogger(__name__)


class AudioStreamException(Exception):
    pass


class HttpStreamClient:
    def __init__(
        self,
        chunk_size: int,
    ):
        super().__init__()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:100.0) Gecko/20100101 Firefox/100.0",
        }
        self.chunk_size = chunk_size

    # Yields a chunk of bytes from a HTTP stream
    async def get_stream(
        self,
        url: ValidUrl,
        stream_name: Optional[str] = None,  # Optional. Used for better logging output
    ) -> AsyncIterator[bytes]:
        try:
            logger.debug(f"{format_stream_name(stream_name)}Fetching stream for: {url}")

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    response.raise_for_status()
                    async for chunk in response.content.iter_chunked(n=self.chunk_size):
                        yield chunk
        except Exception as e:
            raise AudioStreamException(
                f"Unable to fetch stream: {url}. Check your stream URL."
            ) from e


# Base for stream adapters
class AudioStreamAdapter(ABC):
    def __init__(self, http_stream_client: HttpStreamClient):
        super().__init__()
        self.http_stream_client = http_stream_client

    @abstractmethod
    # Yields a chunk of bytes from a stream
    async def get_audio_data(
        self,
        url: ValidUrl,
        countdown: utils.CountdownTimer,
        stream_name: Optional[str] = None,
    ) -> AsyncIterator[bytes]:
        raise NotImplementedError
        yield


# Simple audio stream adapter that fetches data from a HTTP stream for a given duration
class HttpAudioStreamAdapter(AudioStreamAdapter):
    def __init__(
        self,
        http_stream_client: HttpStreamClient,
    ):
        super().__init__(http_stream_client)

    # Yields a chunk of bytes from a HTTP stream
    async def get_audio_data(
        self,
        url: ValidUrl,
        countdown: utils.CountdownTimer,
        stream_name: Optional[str] = None,
    ) -> AsyncIterator[bytes]:
        logger.debug(f"Starting to fetch audio stream for {countdown.duration_total}")
        countdown.start()

        # Keep fetching data from the stream until the countdown expires
        async for chunk in self.http_stream_client.get_stream(url, stream_name):
            yield chunk
            if countdown.is_expired():
                logger.debug("Countdown expired")
                break


# Get data from HLS stream (playlist url from which new segments are fetched continuously)
class HlsAudioStreamAdapter(HttpAudioStreamAdapter):
    def __init__(
        self,
        http_stream_client: HttpStreamClient,
    ):
        super().__init__(http_stream_client)

    # Yields a chunk of bytes from a HLS stream
    async def get_audio_data(
        self,
        url: ValidUrl,
        countdown: utils.CountdownTimer,
        stream_name: Optional[str] = None,
    ) -> AsyncIterator[bytes]:
        WAIT_TIME_SEC = 5  # Time to wait until checking for new segments
        recorded_segments: list[str] = []

        countdown.start()

        # Get initial segments
        new_segments = self._get_new_segments(url, recorded_segments)
        # Start recording from most recent segment
        recorded_segments = new_segments[:-1]

        while not countdown.is_expired():
            new_segments = self._get_new_segments(url, recorded_segments)
            logger.debug(f"{len(new_segments)} new segment(s) found")

            for segment in new_segments:
                async for chunk in self.http_stream_client.get_stream(
                    self._to_url(url, segment), stream_name
                ):
                    yield chunk
                    # Immediately stop if countdown expires
                    if countdown.is_expired():
                        logger.debug("Countdown expired")
                        break

            # Update recorded segments
            recorded_segments.extend(new_segments)

            # Wait before fetching new segments
            logger.debug(
                f"{format_stream_name(stream_name)}Waiting {WAIT_TIME_SEC} seconds before fetching new segments"
            )
            await asyncio.sleep(WAIT_TIME_SEC)

    # Updates internal segment state and returns new segments
    def _get_new_segments(
        self, playlist_url: ValidUrl, old_segments: list[str]
    ) -> list[str]:
        try:
            # Reload playlist
            playlist = m3u8.load(playlist_url)
        except Exception as e:
            raise AudioStreamException(
                f"Unable to fetch stream: {playlist_url}. Check your stream URL."
            ) from e

        # Get all segments not in old
        new_segment_files: list[str] = [segment_file for segment_file in playlist.files if segment_file not in old_segments]  # type: ignore

        # Update state and return new segments
        return new_segment_files

    def _to_url(self, base_url: ValidUrl, segment_file: str) -> ValidUrl:
        return ValidUrl(urljoin(base_url, segment_file))


def format_stream_name(stream_name: Optional[str]) -> str:
    if not stream_name:
        return ""

    return "Stream " + "'" + str(stream_name) + "': "
