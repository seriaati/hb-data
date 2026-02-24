from pydantic import BaseModel, Field

__all__ = ("DriveDisc", "DriveDiscSet")


class DriveDisc(BaseModel):
    id: int = Field(alias="ItemID")
    position: int = Field(alias="Position")
    suit_id: int = Field(alias="SuitID")

    @property
    def icon(self) -> str:
        return f"https://zzz.honeyhunterworld.com/img/item/{self.id}-item_icon_35.webp"


class DriveDiscSet(BaseModel):
    id: int = Field(alias="ID")
    name: str = Field(alias="Name")
    two_set_effect: str = Field(alias="TwoSetEffect")
    four_set_effect: str = Field(alias="FourSetEffect")
    story: str = Field(alias="SuitStory")

    @property
    def icon(self) -> str:
        return f"https://zzz.honeyhunterworld.com/img/art_set/{self.id}-art_set_icon.webp"
