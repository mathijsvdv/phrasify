# SPDX-FileCopyrightText: 2023-present Mathijs van der Vlies <mathijsvdvlies@solcon.nl>
#
# SPDX-License-Identifier: GPL-3.0-or-later
from . import _paths  # noqa: I001, F401
from .__about__ import NAME, __version__  # noqa: F401

import os

from .env import load_env
from .hooks import init_hooks
from .dialogs import init_dialogs
from .logging import setup_logging, get_logger


setup_logging()
logger = get_logger(__name__)


def init_package():
    logger.info("Initializing package")
    load_env()


def init_addon():  # pragma: no cover
    logger.info("Initializing addon")
    init_dialogs()
    init_hooks()


init_package()
if os.getenv("INIT_PHRASIFY_ADDON", "true").lower() == "true":  # pragma: no cover
    init_addon()
