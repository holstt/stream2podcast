import logging
import time
from datetime import timedelta
from pathlib import Path
from threading import Timer
from typing import Callable

from watchdog.events import FileSystemEvent, FileSystemEventHandler

from src.domain.models import PodcastUpdatedEvent
from src.infra.file_reader import PodcastFileService

logger = logging.getLogger(__name__)


# This handler absorbs all file events as long as they occur within the given debounce time
# The debounce time is reset every time a new file event occurs for the same file
# First when the debounce time has passed without any new file events for the given file, the callback is triggered
class FileChangedEventHandler(FileSystemEventHandler):
    # Callback gets passed the path of the file that triggered the event
    def __init__(
        self, debounce_time: timedelta, callback: Callable[[PodcastUpdatedEvent], None]
    ) -> None:
        super().__init__()
        self._callback = callback
        self._debounce_time = debounce_time
        # All file events currently waiting for their debounce time to pass
        self._pending_file_changed_events: dict[
            Path, float
        ] = {}  # File path -> last file event timestamp

    # Triggers on any kind of file change
    def on_any_event(self, event: FileSystemEvent) -> None:  # type: ignore
        logger.debug(f"{event.event_type} - {event.src_path}")
        file_changed_path = Path(event.src_path)

        # Ignore directory changes (as this is always triggered when a file changes)
        # Ignore any changes to the .rss feed files themselves
        if (
            file_changed_path.is_dir()
            or file_changed_path.name
            == PodcastFileService.FEED_FILE_NAME  # TODO: Inject ignore patterns
        ):
            return

        current_time = time.time()
        # Check if event already pending for this path
        if file_changed_path not in self._pending_file_changed_events:
            # Start timer in seperat thread to check on file after debounce time has passed
            self._start_debounce_timer(file_changed_path)

        # Update timestamp of last file event
        self._pending_file_changed_events[file_changed_path] = current_time

    def _start_debounce_timer(self, file_path: Path):
        Timer(
            interval=self._debounce_time.total_seconds(),
            function=lambda: self._raise_if_older_than_debounce(file_path),
        ).start()

    # Check if last file event is older than debounce time -> then trigger file event
    def _raise_if_older_than_debounce(self, file_path: Path) -> None:
        last_event_time = self._pending_file_changed_events[file_path]
        current_time = time.time()
        time_passed_since_last_event = current_time - last_event_time

        if time_passed_since_last_event >= self._debounce_time.total_seconds():
            self._on_file_changed_event(file_path)
            del self._pending_file_changed_events[file_path]
        else:
            # Start a new debounce timer
            # XXX: Maybe just a new thread and a while loop instead of keep starting new timers/threads?
            self._start_debounce_timer(file_path)

    def _on_file_changed_event(self, file_path: Path) -> None:
        logger.info(
            f"File change detected after debounce time ({self._debounce_time}): {file_path}"
        )
        self._callback(PodcastUpdatedEvent(episode_id=file_path))
