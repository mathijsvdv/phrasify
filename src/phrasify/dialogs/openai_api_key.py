import os

from aqt import mw
from aqt.qt import QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout
from aqt.utils import qconnect, showInfo

from phrasify.env import env_set_key


class OpenAIAPIKeyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Set OpenAI API Key")

        self.label = QLabel()
        self.label.setText("OpenAI API Key")

        self.input_field = QLineEdit(self)

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self._handle_key_save)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.input_field)
        self.layout.addWidget(self.save_button)
        self.setLayout(self.layout)

    def _handle_key_save(self):
        self.on_key_save(self.input_field.text())

    def on_key_save(self, openai_api_key: str):
        self.hide()
        env_set_key("OPENAI_API_KEY", openai_api_key)


def add_ankibrain_menu_item(name: str, fn):
    action = mw.ankibrain_menu.addAction(name)
    qconnect(action.triggered, fn)

    # Keep track of added actions for removal later if needed.
    mw.menu_actions.append(action)


def init_openai_api_key_dialog():
    dialog = OpenAIAPIKeyDialog()
    dialog.hide()

    def show_dialog():
        dialog.show()

    action = mw.form.menuTools.addAction("Phrasify - Set OpenAI API Key...")
    qconnect(action.triggered, show_dialog)


def show_missing_open_api_key():
    if "OPENAI_API_KEY" not in os.environ:
        showInfo(
            "Phrasify has loaded, but the OpenAI API key is missing. Please set "
            "it in Tools > Phrasify - Set OpenAI API Key..."
        )
