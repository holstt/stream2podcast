from typing import Iterator
from pydantic import HttpUrl
import requests
import logging
logger = logging.getLogger(__name__)


# Yields a chunk of bytes from a http stream
def fetch_stream_chunk(url: HttpUrl, chunk_size: int) -> Iterator[bytes]:

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:100.0) Gecko/20100101 Firefox/100.0",
    }

    try:
        logging.debug(f"Fetching stream: {url}")
        with requests.get(url, stream=True, headers=headers) as response:
            response.raise_for_status()

            for chunk in response.iter_content(chunk_size=chunk_size):
                yield chunk
    except requests.HTTPError as e:
        raise AudioStreamException(
            f"Unable to fetch stream: {url}. Check your stream URL."
        ) from e


class AudioStreamException(Exception):
    pass
