from __future__ import annotations

import asyncio
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Self

from loguru import logger
from yarl import URL

from hb_data.common.base_client import BaseClient
from hb_data.gi import models

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
    IT = "IT"
    JP = "JP"
    KR = "KR"
    PT = "PT"
    RU = "RU"
    TH = "TH"
    TR = "TR"
    VI = "VI"


HAS_TWO_PARTS = (Language.RU, Language.TH)

BASE_URL = URL("https://gitlab.com/Dimbreath/AnimeGameData/-/raw/master")
TEXT_MAP_URL = BASE_URL / "TextMap"
DATA_URL = BASE_URL / "ExcelBinOutput"
DATA_FILE_NAMES = (
    "BeyondCostumeExcelConfigData",  # MW costumes
    "BydMaterialExcelConfigData",  # MW items
)


class GIClient(BaseClient):
    def __init__(self) -> None:
        super().__init__()
        self._text_maps: dict[Language, dict[str, str]] = {}
        self._data: dict[str, Any] = {}
        self._data_dir /= "gi"

    async def __aenter__(self) -> Self:
        await super().__aenter__()
        await self.read_text_maps()
        await self.read_data()
        return self

    def _get_text_map_file_names(self, *, langs: Iterable[Language] | None = None) -> list[str]:
        file_names = []
        for lang in Language:
            if langs is not None and lang not in langs:
                continue
            if lang in HAS_TWO_PARTS:
                file_names.extend((f"TextMap{lang.value}_0.json", f"TextMap{lang.value}_1.json"))
            else:
                file_names.append(f"TextMap{lang.value}.json")
        return file_names

    async def _read_text_map(self, lang: Language) -> None:
        logger.debug(f"Reading text map for language: {lang}")
        file_name = f"TextMap{lang.value}.json"
        file_path = self._get_file_path(TEXT_MAP_URL / file_name)

        if lang in HAS_TWO_PARTS:
            file_name_part1 = f"TextMap{lang.value}_0.json"
            file_path_part1 = self._get_file_path(TEXT_MAP_URL / file_name_part1)
            text_map_part1 = await self._read_json(file_path_part1)

            file_name_part2 = f"TextMap{lang.value}_1.json"
            file_path_part2 = self._get_file_path(TEXT_MAP_URL / file_name_part2)
            text_map_part2 = await self._read_json(file_path_part2)

            merged_text_map = {**text_map_part1, **text_map_part2}
            self._text_maps[lang] = merged_text_map
        else:
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

    async def download(
        self, *, langs: Iterable[Language] | None = None, force: bool = False
    ) -> None:
        await self._download_files(
            [TEXT_MAP_URL / file_name for file_name in self._get_text_map_file_names(langs=langs)],
            force=force,
        )
        await self.read_text_maps(langs=langs)

        await self._download_files(
            [DATA_URL / f"{file_name}.json" for file_name in DATA_FILE_NAMES], force=force
        )
        await self.read_data()

    def translate(self, text_map_hash: str, *, lang: Language) -> str:
        return self._text_maps.get(lang, {}).get(text_map_hash, text_map_hash)

    def get_mw_costumes(self, *, lang: Language = Language.EN) -> list[models.MWCostume]:
        result: list[models.MWCostume] = []
        data: list[dict[str, Any]] = self._data["BeyondCostumeExcelConfigData"]
        for item in data:
            costume = models.MWCostume.model_validate(item)
            costume.name = self.translate(costume.name, lang=lang)
            result.append(costume)
        return result

    def get_mw_items(self, *, lang: Language = Language.EN) -> list[models.MWItem]:
        result: list[models.MWItem] = []
        data: list[dict[str, Any]] = self._data["BydMaterialExcelConfigData"]
        for item in data:
            mw_item = models.MWItem.model_validate(item)
            mw_item.name = self.translate(mw_item.name, lang=lang)
            mw_item.description = self.translate(mw_item.description, lang=lang)
            result.append(mw_item)
        return result
