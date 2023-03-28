import time
import logging
import argparse

logger = logging.getLogger(__name__)


def get_args_config_path():
    # Load args
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


def setup_logging():
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname)s] %(name)-25s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.Formatter.converter = time.gmtime  # Use UTC
