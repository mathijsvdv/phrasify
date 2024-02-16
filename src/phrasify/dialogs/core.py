from .openai_api_key import init_openai_api_key_dialog, show_missing_open_api_key


def init_dialogs():
    init_openai_api_key_dialog()
    show_missing_open_api_key()
