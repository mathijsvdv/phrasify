from pathlib import Path

ROOT_DIR = Path(__file__).parent
LOGGING_CONFIG_PATH = ROOT_DIR / "logging_config.json"
LIB_DIR = ROOT_DIR / "lib"
USER_FILES_DIR = ROOT_DIR / "user_files"
DOTENV_PATH = USER_FILES_DIR / ".env"
PROMPT_DIR = USER_FILES_DIR / "prompts"
GENERATED_CARDS_DIR = USER_FILES_DIR / "generated_cards"
DEFAULT_N_CARDS = 5
DEFAULT_MIN_CARDS = 3
DEFAULT_SOURCE_LANGUAGE = "English"
DEFAULT_TARGET_LANGUAGE = "Ukrainian"
