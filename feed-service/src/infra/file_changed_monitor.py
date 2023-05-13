import logging
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers.polling import PollingObserver

logger = logging.getLogger(__name__)


# Recursively monitors a directory for file changes
class FileChangedMonitor:
    def __init__(
        self, root_dir: Path, file_changed_handler: FileSystemEventHandler
    ) -> None:
        super().__init__()
        self.root_dir = root_dir
        self.file_changed_handler = file_changed_handler

        # Polling observer is used (instead of default Oberver that uses system events) as system events for files that are being written to by another process are not always triggered on some OS's (e.g. Windows)
        self.observer = PollingObserver()

    # Starts monitoring
    def start(self) -> None:
        logger.info(f"Started monitoring directory for file changes: {self.root_dir}")

        self.observer.schedule(self.file_changed_handler, self.root_dir, recursive=True)  # type: ignore
        self.observer.start()

        try:
            # Keep alive
            while True:
                time.sleep(1)
        finally:
            # Stop and wait for observer to finish
            self.observer.stop()
            self.observer.join()
