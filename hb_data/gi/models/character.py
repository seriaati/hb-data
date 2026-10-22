from enum import StrEnum

from pydantic import BaseModel, Field, field_validator

__all__ = ("Character", "CharacterCostume", "Element")

QUALITY_TO_RARITY = {"QUALITY_ORANGE": 5, "QUALITY_ORANGE_SP": 5, "QUALITY_PURPLE": 4}


class Element(StrEnum):
    PYRO = "Fire"
    HYDRO = "Water"
    ANEMO = "Wind"
    ELECTRO = "Electric"
    DENDRO = "Grass"
    CRYO = "Ice"
    GEO = "Rock"


class CharacterCostume(BaseModel):
    id: int = Field(alias="skinId")
    character_id: int = Field(alias="characterId")
    name: str = Field(alias="nameTextMapHash", coerce_numbers_to_str=True)
    image: str = Field(alias="frontIconName")

    @field_validator("image", mode="after")
    @classmethod
    def __convert_image(cls, v: str) -> str:
        return f"https://enka.network/ui/{v.replace('UI_AvatarIcon_', 'UI_Costume_')}.png"


class Character(BaseModel):
    id: int
    name: str = Field(alias="nameTextMapHash", coerce_numbers_to_str=True)
    rarity: int = Field(alias="qualityType")
    element: Element | None = None
    icon: str = Field(alias="iconName")
    costumes: list[CharacterCostume] = Field(default_factory=list)

    @field_validator("rarity", mode="before")
    @classmethod
    def __convert_rarity(cls, v: str) -> int:
        return QUALITY_TO_RARITY[v]

    @field_validator("icon", mode="after")
    @classmethod
    def __convert_icon(cls, v: str) -> str:
        return f"https://enka.network/ui/{v}.png"
