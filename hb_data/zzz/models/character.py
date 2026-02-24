from typing import Literal

from pydantic import BaseModel, Field, field_validator

from .enums import ElementType, Specialty

__all__ = ("Character",)


class Character(BaseModel):
    id: int = Field(alias="ID")
    name: str = Field(alias="UIName")
    full_name: str = Field(alias="FullName")
    element: ElementType = Field(alias="Elements")
    specialty: Specialty = Field(alias="AvatarSpecialty")
    rarity: int = Field(alias="Rarity")
    faction_name: str = Field(alias="CampName")

    @property
    def icon(self) -> str:
        return f"https://zzz.honeyhunterworld.com/img/character/{self.id}-char_icon.webp"

    @property
    def phase_1_cinema_art(self) -> str:
        return f"https://zzz.honeyhunterworld.com/img/character/{self.id}-char_mindscape1_icon.webp"

    @property
    def phase_2_cinema_art(self) -> str:
        return f"https://zzz.honeyhunterworld.com/img/character/{self.id}-char_mindscape2_icon.webp"

    @property
    def phase_3_cinema_art(self) -> str:
        return f"https://zzz.honeyhunterworld.com/img/character/{self.id}-char_mindscape3_icon.webp"

    @property
    def rarity_str(self) -> Literal["A", "S"]:
        return ("C", "B", "A", "S")[self.rarity - 1]  # pyright: ignore[reportReturnType]

    @field_validator("element", mode="before")
    @classmethod
    def validate_element(cls, v: list[int]) -> int:
        return v[0]
