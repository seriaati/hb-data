from pydantic import BaseModel, Field, field_validator

__all__ = ("Bangboo",)


class Bangboo(BaseModel):
    id: int = Field(alias="ID")
    name: str = Field(alias="Name")
    rarity: int = Field(alias="Rarity")

    @property
    def rarity_str(self) -> str:
        return ("C", "B", "A", "S")[self.rarity - 2]  # pyright: ignore[reportReturnType]

    @property
    def icon(self) -> str:
        return f"https://zzz.honeyhunterworld.com/img/item/{self.id}-item_icon.webp"

    @field_validator("rarity", mode="after")
    @classmethod
    def __convert_rarity(cls, v: int) -> int:
        return v + 1
