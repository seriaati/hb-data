from typing import Literal

from pydantic import BaseModel, Field, field_validator

from .enums import ElementType, Specialty

__all__ = ("Character", "CharacterSkin")


class CharacterSkin(BaseModel):
    id: int = Field(alias="SkinID")
    character_id: int = Field(alias="AvatarID")
    name: str = Field(alias="SkinName")
    description: str = Field(alias="SkinDesc")
    image_name: str = Field(alias="SkinImage")
    tags: list[str] = Field(alias="SkinTags")

    @property
    def image(self) -> str:
        return f"https://enka.network/ui/zzz/{self.image_name}.png"

    @property
    def icon(self) -> str:
        return f"https://static.nanoka.cc/assets/zzz/{self.image_name.replace('Role', 'RoleSelect')}.webp"


class Character(BaseModel):
    id: int = Field(alias="ID")
    name: str = Field(alias="Name")
    full_name: str = Field(alias="FullName")
    element: ElementType = Field(alias="Elements")
    specialty: Specialty = Field(alias="AvatarSpecialty")
    rarity: int = Field(alias="Rarity")
    faction_name: str = Field(alias="CampName")
    skins: list[CharacterSkin] = Field(default_factory=list)

    image: str = ""
    icon: str = ""

    @property
    def phase_1_cinema_art(self) -> str:
        return f"https://enka.network/ui/zzz/Mindscape_{self.id}_1.png"

    @property
    def phase_2_cinema_art(self) -> str:
        return f"https://enka.network/ui/zzz/Mindscape_{self.id}_2.png"

    @property
    def phase_3_cinema_art(self) -> str:
        return f"https://enka.network/ui/zzz/Mindscape_{self.id}_3.png"

    @property
    def rarity_str(self) -> Literal["A", "S"]:
        return ("C", "B", "A", "S")[self.rarity - 2]  # pyright: ignore[reportReturnType]

    @field_validator("element", mode="before")
    @classmethod
    def __validate_element(cls, v: list[int]) -> int:
        return v[0]

    @field_validator("rarity", mode="after")
    @classmethod
    def __convert_rarity(cls, v: int) -> int:
        return v + 1
