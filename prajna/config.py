"""PRAJNA — Configuration loader."""

import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Config:
    """Central configuration object loaded from YAML."""

    _data: dict = field(default_factory=dict, repr=False)

    def __getattr__(self, key: str):
        if key.startswith("_"):
            return super().__getattribute__(key)
        val = self._data.get(key)
        if isinstance(val, dict):
            return Config(_data=val)
        return val

    def __getitem__(self, key: str):
        return self.__getattr__(key)

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def to_dict(self) -> dict:
        return self._data

    @classmethod
    def load(cls, path: Optional[str] = None) -> "Config":
        """Load config from YAML file."""
        if path is None:
            path = Path(__file__).parent.parent / "config" / "default.yaml"
        else:
            path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Config not found: {path}")

        with open(path, "r") as f:
            data = yaml.safe_load(f)

        return cls(_data=data)
