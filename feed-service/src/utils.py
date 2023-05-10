import argparse
import logging
import time

logger = logging.getLogger(__name__)


def read_config_path():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "-c",
        "--config",
        required=False,
        help="Path of yaml config file",
        default="config.yml",
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
