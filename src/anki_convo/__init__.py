# SPDX-FileCopyrightText: 2023-present Mathijs van der Vlies <mathijsvdvlies@solcon.nl>
#
# SPDX-License-Identifier: GPL-3.0-or-later
from . import _paths  # noqa: I001, F401
from .__about__ import NAME, __version__  # noqa: F401

import os

from .env import load_env
from .openai import init_openai
from .hooks import init_hooks
from .logging import setup_logging, get_logger


setup_logging()
logger = get_logger(__name__)


def init_package():
    logger.info("Initializing package")
    load_env()
    init_openai()


def init_addon():
    logger.info("Initializing addon")
    init_hooks()


init_package()
if os.getenv("INIT_ANKI_CONVO_ADDON", "true").lower() == "true":
    init_addon()
