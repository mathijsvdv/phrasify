# SPDX-FileCopyrightText: 2023-present Mathijs van der Vlies <mathijsvdvlies@solcon.nl>
#
# SPDX-License-Identifier: GPL-3.0-or-later
from . import _paths  # noqa: F401 I001

import os
from .env import load_env
from .openai import init_openai
from .addition_filter import init_addition_filter
from .card_count_view import init_card_count_view
from .field_filter import init_field_filter
from .llm_filter import init_llm_filter


def init_package():
    load_env()
    init_openai()


def init_addon():
    init_card_count_view()
    init_field_filter()
    init_addition_filter()
    init_llm_filter()


init_package()
if os.getenv("INIT_ANKI_CONVO_ADDON", "true").lower() == "true":
    init_addon()
