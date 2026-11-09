from typing import Any, Self

from pydantic import BaseModel, Field, field_validator, model_validator

__all__ = ("RelicSet",)


class RelicSet(BaseModel):
    id: int = Field(alias="SetID")
    name: str = Field(alias="SetName")
    is_planar: bool = Field(alias="IsPlanarSuit", default=False)
    icon: str = ""

    @field_validator("name", mode="before")
    @classmethod
    def __extract_name_hash(cls, v: dict[str, Any]) -> str:
        return str(v["Hash"])

    @model_validator(mode="after")
    def __set_icon(self) -> Self:
        # SetIconPath isn't hosted on Enka, so use the head (cavern) or sphere (planar) piece icon
        slot = 5 if self.is_planar else 1
        self.icon = f"https://enka.network/ui/hsr/SpriteOutput/ItemIcon/RelicIcons/IconRelic_{self.id}_{slot}.png"
        return self
