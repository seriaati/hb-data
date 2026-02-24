from typing import Literal

from pydantic import BaseModel, Field, field_validator

from hb_data.zzz.models.enums import Specialty

__all__ = ("Weapon",)


class Weapon(BaseModel):
    id: int = Field(alias="ItemID")
    name: str = Field(alias="Name")
    specialty: Specialty = Field(alias="WeaponSpecialty")
    rarity: int = Field(alias="Rarity")

    @property
    def icon(self) -> str:
        return f"https://zzz.honeyhunterworld.com/img/item/{self.id}-weapon_data_icon.webp"

    @property
    def rarity_str(self) -> Literal["B", "A", "S"]:
        return ("C", "B", "A", "S")[self.rarity - 2]  # pyright: ignore[reportReturnType]

    @field_validator("rarity", mode="after")
    @classmethod
    def __convert_rarity(cls, v: int) -> int:
        return v + 1
