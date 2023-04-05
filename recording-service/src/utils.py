from pathlib import Path
import time
import logging
import argparse
import os


from pydantic import DirectoryPath

logger = logging.getLogger(__name__)


def read_config_path():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "-c",
        "--config",
        required=False,
        help="Path of json config file",
        default="config.json",
    )
    args = vars(ap.parse_args())

    # Get config from args
    config_file_path = args["config"]

    return config_file_path


def setup_logging(level: int = logging.INFO):
    logging.basicConfig(
        level=level,
        format="[%(asctime)s] [%(levelname)s] %(name)-25s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.Formatter.converter = time.gmtime  # Use UTC


def ensure_writable_dir_created(dir_value: Path) -> DirectoryPath:
    os.makedirs(dir_value, exist_ok=True)

    # Test if we have write access to the output directory
    if not os.access(dir_value, os.W_OK | os.X_OK):
        raise IOError(f"Missing write permissions to directory {dir_value}")

    return dir_value
