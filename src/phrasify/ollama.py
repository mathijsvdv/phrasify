import os


def get_ollama_url():
    """Get the URL where Ollama is running from the environment."""
    return os.getenv("OLLAMA_URL", "http://localhost:11434")
