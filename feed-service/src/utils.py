import argparse
import logging
import time
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


def read_yml_file(file_path: Path) -> dict[str, Any] | Any:
    logger.debug(f"Reading yml file: {file_path}")
    with open(file_path, "r") as file:
        return yaml.safe_load(file)


def get_config_path_from_args():
    args = get_args()
    config_file_path = args["config"]
    return config_file_path


def get_args():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "-c",
        "--config",
        required=False,
        help="Path of yaml config file",
        default="config.yml",
    )
    args = vars(ap.parse_args())
    return args


def setup_logging(level: int = logging.INFO):
    logging.basicConfig(
        level=level,
        format="[%(asctime)s] [%(levelname)s] %(name)-25s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.Formatter.converter = time.gmtime  # Use UTC
