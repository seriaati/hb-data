from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable


def find_key_by_value(data: dict, value: Any) -> str:
    return next(k for k, v in data.items() if v == value)


@dataclass
class DeobfuscatedField:
    name: str
    finder: Callable[[dict], str]  # receives the obfuscated dict, returns the obfuscated key


class DeobfuscatorMeta(type):
    def __new__(mcs, name: str, bases: tuple, namespace: dict[str, Any]) -> type:
        fields = {
            key: value for key, value in namespace.items() if isinstance(value, DeobfuscatedField)
        }
        namespace["_fields"] = fields
        return super().__new__(mcs, name, bases, namespace)


class BaseDeobfuscator(metaclass=DeobfuscatorMeta):
    def __init__(self, data: dict) -> None:
        self._data = data
        self._list_key: str = next(iter(data))
        self._entries: list[dict] = data[self._list_key]
        self._key_map: dict[str, str] = {}
        self._fields: dict[str, DeobfuscatedField]

    def generate_key_map(self) -> dict[str, str]:
        sample = self._entries[0]
        self._key_map = {}
        for field_def in self._fields.values():
            obfuscated_key = field_def.finder(sample)
            self._key_map[field_def.name] = obfuscated_key
        return self._key_map

    def deobfuscate(self) -> list[dict[str, Any]]:
        if not self._key_map:
            self.generate_key_map()

        return [
            {
                readable: entry[obf_key]
                for readable, obf_key in self._key_map.items()
                if obf_key in entry
            }
            for entry in self._entries
        ]
