# SPDX-FileCopyrightText: 2023-present Mathijs van der Vlies <mathijsvdvlies@solcon.nl>
#
# SPDX-License-Identifier: GPL-3.0-or-later
from . import _paths  # noqa: I001, F401

import logging.config
import os

from .env import load_env
from .openai import init_openai
from .addition_filter import init_addition_filter
from .card_count_view import init_card_count_view
from .field_filter import init_field_filter
from .llm_filter import init_llm_filter
from .logging_config import setup_logging


setup_logging()
logger = logging.getLogger(__name__)


def init_package():
    logger.info("Initializing package")
    load_env()
    init_openai()


def init_addon():
    logger.info("Initializing addon")
    init_card_count_view()
    init_field_filter()
    init_addition_filter()
    init_llm_filter()


init_package()
if os.getenv("INIT_ANKI_CONVO_ADDON", "true").lower() == "true":
    init_addon()
