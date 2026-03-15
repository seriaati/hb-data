from pydantic import BaseModel, Field, field_validator

__all__ = ("DriveDisc", "DriveDiscSet")


class DriveDisc(BaseModel):
    id: int = Field(alias="ItemID")
    position: int = Field(alias="Position")
    suit_id: int = Field(alias="SuitID")
    icon: str = Field(alias="ItemIcon")

    @field_validator("icon", mode="after")
    @classmethod
    def __convert_icon(cls, v: str) -> str:
        url = "https://static.nanoka.cc/assets/zzz/{name}.webp"
        return url.format(name=v.rsplit("/", maxsplit=1)[-1].split(".", maxsplit=1)[0])


class DriveDiscSet(BaseModel):
    id: int = Field(alias="ID")
    name: str = Field(alias="Name")
    two_set_effect: str = Field(alias="TwoSetEffect")
    four_set_effect: str = Field(alias="FourSetEffect")
    story: str = Field(alias="SuitStory")
    icon: str = Field(alias="SuitIcon")

    @field_validator("icon", mode="after")
    @classmethod
    def __convert_icon(cls, v: str) -> str:
        url = "https://static.nanoka.cc/assets/zzz/{name}.webp"
        return url.format(name=v.rsplit("/", maxsplit=1)[-1].split(".", maxsplit=1)[0])
