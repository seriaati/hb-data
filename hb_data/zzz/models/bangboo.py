from typing import Literal

from pydantic import BaseModel, Field, field_validator

__all__ = ("Bangboo",)


class Bangboo(BaseModel):
    id: int = Field(alias="ID")
    name: str = Field(alias="Name")
    rarity: int = Field(alias="Rarity")

    icon: str = ""

    @property
    def rarity_str(self) -> Literal["B", "A", "S"]:
        return ("C", "B", "A", "S")[self.rarity - 2]  # pyright: ignore[reportReturnType]

    @field_validator("rarity", mode="after")
    @classmethod
    def __convert_rarity(cls, v: int) -> int:
        return v + 1
