import argparse
import os
import logging
from pathlib import Path
import asyncio
from src.recorder_service import start_recording
from src.utils import load_config
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)-25s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logging.Formatter.converter = time.gmtime  # Use UTC


logger = logging.getLogger(__name__)

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


async def main():
    config_path = args["config"]
    if not Path(config_path).exists():
        raise IOError(f"No config file found at path: {config_path}")

    config = load_config(config_path)

    # Create output dir
    if not os.path.exists(config.output_directory):
        logging.info(f"Creating output directory {config.output_directory}")
        os.mkdir(config.output_directory)

    await start_recording(config)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.exception(f"Unhandled exception occurred: {e}")
        raise e
