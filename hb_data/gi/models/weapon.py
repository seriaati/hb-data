from enum import StrEnum

from pydantic import BaseModel, Field, field_validator

__all__ = ("Weapon", "WeaponType")


class WeaponType(StrEnum):
    SWORD = "WEAPON_SWORD_ONE_HAND"
    CLAYMORE = "WEAPON_CLAYMORE"
    POLEARM = "WEAPON_POLE"
    CATALYST = "WEAPON_CATALYST"
    BOW = "WEAPON_BOW"


class Weapon(BaseModel):
    id: int
    name: str = Field(alias="nameTextMapHash", coerce_numbers_to_str=True)
    rarity: int = Field(alias="rankLevel")
    type: WeaponType = Field(alias="weaponType")
    icon: str

    @field_validator("icon", mode="after")
    @classmethod
    def __convert_icon(cls, v: str) -> str:
        return f"https://enka.network/ui/{v}.png"
