import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

import src.utils as utils
from src.domain.models import ValidUrl

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class AppConfig:
    base_dir: Path
    base_url: ValidUrl
    should_update_feeds_on_startup: bool = False


class YamlConfigParser:
    # Creates a config object from the YAML file at the given path
    def parse(self, file_path: Path) -> AppConfig:
        logger.info(f"Loading config from YAML file: {file_path}")
        config_data = self._read_yaml(file_path)
        config_obj = self._parse(config_data)
        logger.info("Config loaded successfully")
        return config_obj

    # Returns the raw data from the YAML file at the given path
    def _read_yaml(self, file_path: Path) -> dict[str, Any]:
        try:
            data = utils.read_yml_file(file_path)

        except FileNotFoundError as e:
            raise ConfigError(f"File not found: {file_path}") from e
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML file: {file_path}") from e
        if not isinstance(data, dict):
            raise ConfigError(f"Invalid YAML file: {file_path}")

        return data

    # Validates and creates a config object from the given data
    def _parse(self, data: dict[str, Any]) -> AppConfig:
        try:
            base_dir = Path(data["base_directory"]).resolve()

            if not os.access(base_dir, os.R_OK):  # XXX: Move resp. to repo? (infra)
                raise ConfigError(
                    f"Directory does not exist or is not readable: {base_dir}"
                )

            base_url = ValidUrl(data["base_url"])
            should_update_feeds_on_startup = data.get(
                "should_update_feeds_on_startup", False
            )
        except KeyError as e:
            raise ConfigError(f"Missing key: {e}") from e

        return AppConfig(base_dir, base_url, should_update_feeds_on_startup)
