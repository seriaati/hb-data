from enum import StrEnum

from pydantic import BaseModel, Field, field_validator

__all__ = ("Character", "Element")

QUALITY_TO_RARITY = {"QUALITY_ORANGE": 5, "QUALITY_ORANGE_SP": 5, "QUALITY_PURPLE": 4}


class Element(StrEnum):
    PYRO = "Fire"
    HYDRO = "Water"
    ANEMO = "Wind"
    ELECTRO = "Electric"
    DENDRO = "Grass"
    CRYO = "Ice"
    GEO = "Rock"


class Character(BaseModel):
    id: int
    name: str = Field(alias="nameTextMapHash", coerce_numbers_to_str=True)
    rarity: int = Field(alias="qualityType")
    element: Element | None = None
    icon: str = Field(alias="iconName")

    @field_validator("rarity", mode="before")
    @classmethod
    def __convert_rarity(cls, v: str) -> int:
        return QUALITY_TO_RARITY[v]

    @field_validator("icon", mode="after")
    @classmethod
    def __convert_icon(cls, v: str) -> str:
        return f"https://enka.network/ui/{v}.png"
