import logging

from src import config, dependency_resolver, utils
from src.config import AppConfig

logger = logging.getLogger(__name__)


def main(app_config: AppConfig):
    deps = dependency_resolver.resolve(app_config)
    if app_config.should_update_feeds_on_startup:
        deps.usecase.generate_feed(podcast_id=app_config.base_dir.name)

    deps.directory_monitor.start()


if __name__ == "__main__":
    # utils.setup_logging()
    utils.setup_logging(logging.DEBUG)
    try:
        config_file_path = utils.get_config_path_from_args()
        app_config = config.YamlConfigParser().parse(config_file_path)
        main(app_config)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.exception(f"Unhandled exception occurred: {e}")
        raise e
