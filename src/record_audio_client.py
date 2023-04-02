from abc import ABC, abstractmethod
from datetime import timedelta
import time
import logging
from typing import BinaryIO, Callable, Iterator
from pydantic import HttpUrl
from datetime import timedelta
from pydantic import HttpUrl
import m3u8  # type: ignore
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class StreamRecorder(ABC):
    def __init__(self, url: HttpUrl, audio_format: str) -> None:
        super().__init__()
        self._url = url
        self.audio_format = audio_format

    @abstractmethod
    def record(
        self,
        duration: timedelta,
        output_stream: BinaryIO,
        get_chunk: Callable[[HttpUrl, int], Iterator[bytes]],
    ) -> None:
        pass


# Records from a HLS stream (playlist url from which new segments are fetched continuously)
class HSLStreamRecorder(StreamRecorder):
    def __init__(self, url: HttpUrl):
        super().__init__(url, audio_format= "mp4")

    def record(
        self,
        duration: timedelta,
        output_stream: BinaryIO,
        get_chunk: Callable[[HttpUrl, int], Iterator[bytes]],
    ) -> None:

        WAIT_TIME_SEC = 10  # Time to wait until checking for new segments
        CHUNK_SIZE = 1024  # Read 1KB at a time

        end_time = time.time() + duration.total_seconds()
        fetcher = SegmentFetcher(self._url)
        segments = fetcher.get_new_segments(old_segments=[])
        logger.debug(f"Last segment in playlist: {segments[-1]}")

        while time.time() < end_time:
            new_segments = fetcher.get_new_segments(old_segments=segments)

            # Record new segments
            for segment in new_segments:  # type: ignore

                logger.debug(f"Writing segment {segment} to file...")  # type: ignore
                for chunk in get_chunk(segment, CHUNK_SIZE):
                    if chunk:
                        output_stream.write(chunk)

            segments.extend(new_segments)

            time.sleep(WAIT_TIME_SEC)


# Records from an ICY stream (single url)
class ICYStreamRecorder(StreamRecorder):
    def __init__(self, url: HttpUrl):
        super().__init__(url,audio_format= "mp3")

    def record(
        self,
        duration: timedelta,
        output_stream: BinaryIO,
        get_chunk: Callable[[HttpUrl, int], Iterator[bytes]],
    ) -> None:
        end_time = time.time() + duration.total_seconds()

        CHUNK_SIZE = 32 * 1024  # Read 32KB at a time
        
        # NB: ICY stream does not terminate. We just read the next chunk until we want to stop
        for chunk in get_chunk(self._url, CHUNK_SIZE): 
            if chunk:
                output_stream.write(chunk)
            # Check if recording time is over
            if time.time() > end_time:
                break


# Fetches new segments from a HLS stream 
class SegmentFetcher:
    def __init__(self, playlist_url: str):
        super().__init__()
        self.playlist_url = playlist_url


    def get_new_segments(self, old_segments: list[HttpUrl]) -> list[HttpUrl]:
        # Load new playlist
        playlist = m3u8.load(self.playlist_url)  # type: ignore

        # Get all segments not in segment_files
        new_segments: list[HttpUrl] = [self._to_url(segment) for segment in playlist.files if self._to_url(segment) not in old_segments]  # type: ignore

        logger.debug(f"{len(new_segments)} new segments found")

        return new_segments


    def _to_url(self, segment: str) -> HttpUrl:
        return HttpUrl(urljoin(self.playlist_url, segment), scheme="https")

