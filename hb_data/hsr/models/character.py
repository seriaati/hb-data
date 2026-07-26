from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator

__all__ = ("Character", "Element", "Path")

RARITY_MAP = {"CombatPowerAvatarRarityType4": 4, "CombatPowerAvatarRarityType5": 5}


class Element(StrEnum):
    PHYSICAL = "Physical"
    FIRE = "Fire"
    ICE = "Ice"
    THUNDER = "Thunder"
    WIND = "Wind"
    QUANTUM = "Quantum"
    IMAGINARY = "Imaginary"


class Path(StrEnum):
    DESTRUCTION = "Warrior"
    THE_HUNT = "Rogue"
    ERUDITION = "Mage"
    HARMONY = "Shaman"
    NIHILITY = "Warlock"
    PRESERVATION = "Knight"
    ABUNDANCE = "Priest"
    REMEMBRANCE = "Memory"
    ELATION = "Elation"


class Character(BaseModel):
    id: int = Field(alias="AvatarID")
    name: str = Field(alias="AvatarName")
    rarity: int = Field(alias="Rarity")
    element: Element = Field(alias="DamageType")
    path: Path = Field(alias="AvatarBaseType")
    icon: str = Field(alias="AvatarSideIconPath")

    @field_validator("name", mode="before")
    @classmethod
    def __extract_name_hash(cls, v: dict[str, Any]) -> str:
        return str(v["Hash"])

    @field_validator("rarity", mode="before")
    @classmethod
    def __convert_rarity(cls, v: str) -> int:
        return RARITY_MAP[v]

    @field_validator("icon", mode="after")
    @classmethod
    def __convert_icon(cls, v: str) -> str:
        return f"https://enka.network/ui/hsr/{v}"
