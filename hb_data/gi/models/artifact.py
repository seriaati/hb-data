from pydantic import BaseModel, Field, field_validator

__all__ = ("ArtifactSet",)


class ArtifactSet(BaseModel):
    id: int = Field(alias="setId")
    name: str = Field(alias="nameTextMapHash", coerce_numbers_to_str=True)
    icon: str = Field(alias="setIcon")

    @field_validator("icon", mode="after")
    @classmethod
    def __convert_icon(cls, v: str) -> str:
        return f"https://enka.network/ui/{v}.png"
