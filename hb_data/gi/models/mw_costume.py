from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

__all__ = ("MWCostume", "MWItem")


class MWCostume(BaseModel):
    id: int = Field(alias="costumeId")
    name: str = Field(alias="nameTextMapHash", coerce_numbers_to_str=True)


class MWItem(BaseModel):
    id: int = Field(alias="id")
    name: str = Field(alias="nameTextMapHash", coerce_numbers_to_str=True)
    description: str = Field(alias="descTextMapHash", coerce_numbers_to_str=True)
    rarity: int = Field(alias="rankLevel")
    icon: str

    @field_validator("icon", mode="after")
    @classmethod
    def __convert_icon(cls, v: str) -> str:
        return f"https://starward-static.scighost.com/game-assets/genshin/beyond/{v}.png"
