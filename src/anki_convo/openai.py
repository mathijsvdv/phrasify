import os


def get_openai_api_key():
    """Get the OpenAI API key from the environment."""
    return os.getenv("OPENAI_API_KEY")


OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"
