from __future__ import annotations

import asyncio
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Self

from loguru import logger
from yarl import URL

from hb_data.common.base_client import BaseClient
from hb_data.hsr import models

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path


class Language(StrEnum):
    CHS = "CHS"
    CHT = "CHT"
    DE = "DE"
    EN = "EN"
    ES = "ES"
    FR = "FR"
    ID = "ID"
    JP = "JP"
    KR = "KR"
    PT = "PT"
    RU = "RU"
    TH = "TH"
    VI = "VI"


UPSTREAM_BASE_URL = URL("https://gitlab.com/Dimbreath/turnbasedgamedata/-/raw/main")
TEXT_MAP_URL = URL(
    "https://raw.githubusercontent.com/seriaati/hb-data/refs/heads/main/textmaps/hsr"
)
DATA_URL = UPSTREAM_BASE_URL / "ExcelOutput"
DATA_FILE_NAMES = ("AvatarConfig",)  # Characters

# Trailblazer names resolve to the "{NICKNAME}" placeholder; this sentinel key
# translates to "Trailblazer" in all languages and is used instead.
# scripts/generate_textmaps.py locates the upstream entry by its EN value and
# writes it under this key, so an upstream re-key self-heals on regeneration.
TRAILBLAZER_NAME_HASH = "6354779731002018877"


class HSRClient(BaseClient):
    def __init__(self) -> None:
        super().__init__()
        self._text_maps: dict[Language, dict[str, str]] = {}
        self._data: dict[str, Any] = {}
        self._data_dir /= "hsr"

    async def __aenter__(self) -> Self:
        await super().__aenter__()
        await self.download()
        return self

    def _get_text_map_file_names(self, *, langs: Iterable[Language] | None = None) -> list[str]:
        return [f"TextMap{lang.value}.json" for lang in Language if langs is None or lang in langs]

    async def _read_text_map(self, lang: Language) -> None:
        logger.debug(f"Reading text map for language: {lang}")
        file_name = f"TextMap{lang.value}.json"
        file_path = self._get_file_path(TEXT_MAP_URL / file_name)
        self._text_maps[lang] = await self._read_json(file_path)

    async def _read_data(self, file_path: Path) -> None:
        file_name = file_path.stem
        self._data[file_name] = await self._read_json(file_path)

    async def read_text_maps(self, *, langs: Iterable[Language] | None = None) -> None:
        async with asyncio.TaskGroup() as tg:
            for lang in Language:
                if langs is not None and lang not in langs:
                    continue
                tg.create_task(self._read_text_map(lang))

    async def read_data(self) -> None:
        async with asyncio.TaskGroup() as tg:
            for file_name in DATA_FILE_NAMES:
                file_path = self._get_file_path(DATA_URL / f"{file_name}.json")
                tg.create_task(self._read_data(file_path))

    async def download_data_tables(self, *, force: bool = False) -> None:
        await self._download_files(
            [DATA_URL / f"{file_name}.json" for file_name in DATA_FILE_NAMES], force=force
        )
        await self.read_data()

    async def download(
        self, *, langs: Iterable[Language] | None = None, force: bool = False
    ) -> None:
        await self._download_files(
            [TEXT_MAP_URL / file_name for file_name in self._get_text_map_file_names(langs=langs)],
            force=force,
        )
        await self.read_text_maps(langs=langs)
        await self.download_data_tables(force=force)

    def translate(self, text_map_hash: str, *, lang: Language) -> str:
        return self._text_maps.get(lang, {}).get(text_map_hash, text_map_hash)

    def get_characters(self, *, lang: Language = Language.EN) -> list[models.Character]:
        result: list[models.Character] = []
        data: list[dict[str, Any]] = self._data["AvatarConfig"]

        for item in data:
            character = models.Character.model_validate(item)
            character.name = self.translate(character.name, lang=lang)
            if character.name == "{NICKNAME}":
                character.name = self.translate(TRAILBLAZER_NAME_HASH, lang=lang)
            result.append(character)

        return result
