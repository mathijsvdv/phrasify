# SPDX-FileCopyrightText: 2023-present Mathijs van der Vlies <mathijsvdvlies@solcon.nl>
#
# SPDX-License-Identifier: GPL-3.0-or-later
from . import _paths  # noqa: F401 I001

from pathlib import Path
import json

import openai

from .addition_filter import init_addition_filter
from .card_count_view import init_card_count_view
from .field_filter import init_field_filter

# If we want to support async requests, we need the following additional dependencies:
# aiohttp, aiosignal, async-timeout, charset-normalizer, frozenlist, multidict, yarl

# import importlib
# openai_dependencies = [
#     "aiohttp", "aiosignal", "async_timeout", "charset_normalizer", "frozenlist",
#     "multidict", "yarl", "tqdm", "requests"
# ]


# for dependency in openai_dependencies:
#     try:
#         importlib.import_module(dependency)
#     except ModuleNotFoundError as e:
#         print(f"Could not find openai dependency `{dependency}`")
#         print(e)
#     else:
#         print(f"Successfully imported dependency `{dependency}`!")

config_path = Path(__file__).parent / "config.json"
with open(config_path) as f:
    config = json.load(f)

openai.api_key = config["openaiApiKey"]

# completion = openai.ChatCompletion.create(
#   model="gpt-3.5-turbo",
#   messages=[
#     {"role": "system", "content": "You are a poetic assistant, skilled in explaining complex programming concepts "
#                                   "with creative flair."},
#     {"role": "user", "content": "Compose a poem that explains the concept of recursion in programming."}
#   ]
# )

# print(completion.choices[0].message)


def init_addon():
    init_card_count_view()
    init_field_filter()
    init_addition_filter()


init_addon()
