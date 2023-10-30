import os

import openai


def init_openai():
    openai.api_key = os.getenv("OPENAI_API_KEY")
