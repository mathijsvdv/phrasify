import json
from dataclasses import dataclass


@dataclass
class TranslationCard:
    source: str = ""
    target: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "TranslationCard":
        return cls(**d)

    def to_dict(self) -> dict:
        return {"source": self.source, "target": self.target}

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    def __hash__(self):
        return hash(self.source) ^ hash(self.target)
