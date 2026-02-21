from __future__ import annotations

from pydantic import BaseModel, Field

__all__ = ("Weapon",)


class Weapon(BaseModel):
    id: int = Field(alias="ItemID")
    name: str = Field(alias="Name")
