from pathlib import Path

from dotenv import load_dotenv


def load_env():
    dotenv_path = Path(__file__).parent / "user_files" / ".env"
    load_dotenv(dotenv_path)
