import logging
import os
from pathlib import Path
from typing import Any, AsyncIterator

import yaml

from src.models import RecordingSchedule

logger = logging.getLogger(__name__)


# Custom exception for AudioSaver
class AudioStorageError(Exception):
    pass


class AudioStorageAdapter:  # XXX: FileRepo
    def __init__(self) -> None:
        super().__init__()
        # self.audio_format = audio_format

    async def save(  # XXX: Dto with binary data and domain object? .save(audio_file: AudioFile)
        self,
        audio_data_iterator: AsyncIterator[bytes],
        output_path: Path,
    ):
        # "wb" is write binary
        try:
            with open(output_path, "wb") as f:
                async for chunk in audio_data_iterator:
                    f.write(chunk)

            logger.info(f"Audio file saved: {output_path}")

        except Exception as e:
            raise AudioStorageError(
                f"An error occured while writing audio file: {output_path}"
            ) from e


def ensure_dir_with_metadata(directory: Path, metadata: dict[str, Any]) -> Path:
    _ensure_dir(directory)
    _write_meta_data(directory, metadata)
    return directory


def _ensure_dir(directory: Path):
    # Create dir for audio files if it doesn't exist
    os.makedirs(directory, exist_ok=True)

    # Test if we have write access to the output directory
    if not os.access(directory, os.W_OK | os.X_OK):
        raise IOError(f"Missing write permissions to directory {directory}")


# Create a file with the meta data if it doesn't exist.
def _write_meta_data(directory: Path, metadata: dict[str, Any]):
    metadata_file = directory / "metadata.yml"
    if not metadata_file.exists():
        with open(metadata_file, "w") as f:
            yaml.dump(metadata, f, allow_unicode=True)
