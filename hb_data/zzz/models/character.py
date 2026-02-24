from pydantic import BaseModel, Field, field_validator

from .enums import ElementType, Specialty

__all__ = ("Character",)


class Character(BaseModel):
    id: int = Field(alias="ID")
    name: str = Field(alias="UIName")
    element: ElementType = Field(alias="Elements")
    specialty: Specialty = Field(alias="AvatarSpecialty")

    @field_validator("element", mode="before")
    @classmethod
    def validate_element(cls, v: list[int]) -> int:
        return v[0]
