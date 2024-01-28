class AnkiConvoError(Exception):
    """Base class for exceptions in this module."""

    def __init__(self, message=None):
        self._message = message

    def __str__(self):
        msg = self._message or "<empty message>"
        return msg

    @property
    def user_message(self):
        return self._message


class LLMError(AnkiConvoError):
    """Exceptions raised by LLMs."""

    pass


class LLMParsingError(AnkiConvoError):
    """Exceptions raised while parsing LLM output."""

    pass


class ChainError(AnkiConvoError):
    """Exceptions raised by Chains."""

    pass


class CardGenerationError(AnkiConvoError):
    """Exceptions raised while generating cards."""

    pass
