from pathlib import Path
from typing import AsyncIterator

from src.models import RecordingSchedule


# Custom exception for AudioSaver
class AudioStorageError(Exception):
    pass


class AudioStorageAdapter:
    def __init__(self, audio_format: str) -> None:
        super().__init__()
        self.audio_format = audio_format

    async def store_audio_data(
        self,
        audio_data_iterator: AsyncIterator[bytes],
        output_path: Path,
        audio_metadata: RecordingSchedule,
    ):
        # "wb" is write binary
        try:
            with open(output_path, "wb") as f:
                async for chunk in audio_data_iterator:
                    f.write(chunk)

        except Exception as e:
            raise AudioStorageError(
                f"An error occured while writing audio file: {output_path}"
            ) from e
