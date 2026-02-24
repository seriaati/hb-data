from pydantic import BaseModel, Field

__all__ = ("Bangboo",)


class Bangboo(BaseModel):
    id: int = Field(alias="ID")
    name: str = Field(alias="Name")

    @property
    def icon(self) -> str:
        return f"https://zzz.honeyhunterworld.com/img/item/{self.id}-item_icon.webp"
