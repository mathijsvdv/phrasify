class PhrasifyError(Exception):
    """Base class for exceptions in this module."""

    def __init__(self, message=None):
        self._message = message

    def __str__(self):
        msg = self._message or "<empty message>"
        return msg

    @property
    def user_message(self):
        return self._message


class LLMError(PhrasifyError):
    """Exceptions raised by LLMs."""

    pass


class LLMParsingError(PhrasifyError):
    """Exceptions raised while parsing LLM output."""

    pass


class ChainError(PhrasifyError):
    """Exceptions raised by Chains."""

    pass


class CardGenerationError(PhrasifyError):
    """Exceptions raised while generating cards."""

    pass
