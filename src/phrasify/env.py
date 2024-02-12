import os

from dotenv import load_dotenv, set_key

from phrasify.constants import DOTENV_PATH


def load_env():
    load_dotenv(DOTENV_PATH)


def env_set_key(key: str, value: str):
    set_key(DOTENV_PATH, key, value)
    os.environ[key] = value
