import logging

import yaml

from ._paths import ROOT_DIR

LOGGING_CONFIG_PATH = ROOT_DIR / "logging_config.yaml"


def setup_logging():
    with open(LOGGING_CONFIG_PATH) as f:
        config = yaml.safe_load(f)

    logging.config.dictConfig(config)
