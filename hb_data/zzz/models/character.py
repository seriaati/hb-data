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

    @property
    def icon(self) -> str:
        return f"https://zzz.honeyhunterworld.com/img/character/{self.id}-char_icon.webp"

    @field_validator("element", mode="before")
    @classmethod
    def validate_element(cls, v: list[int]) -> int:
        return v[0]
