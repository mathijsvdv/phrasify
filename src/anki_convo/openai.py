import openai

from .config import config


def init_openai():
    openai.api_key = config["openaiApiKey"]
