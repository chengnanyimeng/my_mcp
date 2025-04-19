import os

from config.logger_config import logger


def path_finder(target: str):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(base_dir)
    services_dir = os.path.join(project_root, target)
    logger.info(f"Path Finder: {services_dir}")
    return services_dir
