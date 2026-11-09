from typing import Any

from pydantic import BaseModel, Field, field_validator

from hb_data.hsr.models.character import Path

__all__ = ("LightCone",)

RARITY_MAP = {
    "CombatPowerLightconeRarity3": 3,
    "CombatPowerLightconeRarity4": 4,
    "CombatPowerLightconeRarity5": 5,
}


class LightCone(BaseModel):
    id: int = Field(alias="EquipmentID")
    name: str = Field(alias="EquipmentName")
    rarity: int = Field(alias="Rarity")
    path: Path = Field(alias="AvatarBaseType")
    icon: str = Field(alias="ItemIconPath")

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
