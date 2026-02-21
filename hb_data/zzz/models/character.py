from __future__ import annotations

import enum

from pydantic import BaseModel, Field, field_validator

__all__ = ("Character", "ElementType", "Specialty")


class ElementType(enum.IntEnum):
    PHYSICAL = 200
    FIRE = 201
    ICE = 202
    ELECTRIC = 203
    ETHER = 205


class Specialty(enum.IntEnum):
    ATTACK = 1
    STUN = 2
    ANOMALY = 3
    SUPPORT = 4
    DEFENSE = 5
    RUPTURE = 6


class Character(BaseModel):
    id: int = Field(alias="ID")
    name: str = Field(alias="UIName")
    element: ElementType = Field(alias="Elements")
    specialty: Specialty = Field(alias="Specialty")

    @field_validator("element", mode="before")
    @classmethod
    def validate_element(cls, v: list[int]) -> int:
        return v[0]
