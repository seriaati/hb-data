from __future__ import annotations

from pydantic import BaseModel, Field

__all__ = ("MWCostume",)


class MWCostume(BaseModel):
    id: int = Field(alias="costumeId")
    name: str = Field(alias="nameTextMapHash", coerce_numbers_to_str=True)
