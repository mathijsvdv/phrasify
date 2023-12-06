import logging
import logging.config
from typing import Optional

import yaml

from .__about__ import NAME
from .constants import LOGGING_CONFIG_PATH


def setup_logging():
    with open(LOGGING_CONFIG_PATH) as f:
        config = yaml.safe_load(f)

    logging.config.dictConfig(config)


def rename_module(module_name: str, package_name: Optional[str] = None):
    """Rename a module to replace the package name with the predefined package name

    This is necessary because in the Anki addon, the package may be loaded in a folder
    named with the plugin ID, rather than the package name.
    """
    if package_name is None:
        package_name = NAME

    name_components = module_name.split(".")
    return ".".join([package_name] + name_components[1:])


def get_logger(module_name: str):
    return logging.getLogger(rename_module(module_name))
