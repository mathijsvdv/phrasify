from dataclasses import dataclass
from enum import Enum


class CardSide(Enum):
    """Side of the card."""

    FRONT = "front"
    BACK = "back"

    @classmethod
    def from_str(cls, s: str) -> "CardSide":
        """Get the CardSide from the string."""
        if s.lower() in ("front", "f"):
            return cls.FRONT
        elif s.lower() in ("back", "b"):
            return cls.BACK
        else:
            msg = f"Invalid side: {s}"
            raise ValueError(msg)


def _is_non_empty_string(s: str) -> bool:
    return isinstance(s, str) and s


@dataclass
class TextCard:
    front: str
    back: str

    def __post_init__(self):
        if not (_is_non_empty_string(self.front) and _is_non_empty_string(self.back)):
            msg = f"Front and back must be non-empty strings: {self}"
            raise ValueError(msg)

    @classmethod
    def from_dict(cls, d: dict) -> "TextCard":
        return cls(front=d["front"], back=d["back"])

    def to_dict(self) -> dict:
        return {"front": self.front, "back": self.back}
