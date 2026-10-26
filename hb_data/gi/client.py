from __future__ import annotations

import asyncio
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Self

from loguru import logger
from pydantic import ValidationError
from yarl import URL

from hb_data.common.base_client import BaseClient
from hb_data.gi import deob, models

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


UPSTREAM_BASE_URL = URL("https://gitlab.com/Dimbreath/AnimeGameData2/-/raw/main")
TEXT_MAP_URL = URL("https://raw.githubusercontent.com/seriaati/hb-data/refs/heads/main/textmaps/gi")
DATA_URL = UPSTREAM_BASE_URL / "ExcelBinOutput"
DATA_FILE_NAMES = (
    "AvatarExcelConfigData",  # Characters
    "AvatarSkillDepotExcelConfigData",  # Character skill depots (for element)
    "AvatarSkillExcelConfigData",  # Character skills (for element)
    "AvatarCostumeExcelConfigData",  # Character costumes
    "BeyondCostumeDrawingExcelConfigData",  # MW costume catalogs
    "BeyondCostumeExcelConfigData",  # MW costumes
    "BeyondEmojiExcelConfigData",  # MW emojis
    "BydMaterialExcelConfigData",  # MW items
)
# Only source of MW pose icon names; the data dump has icon hashes only
STARWARD_MW_ITEMS_URL = URL(
    "https://starward-static.scighost.com/game-assets/genshin/GenshinBeyondGachaInfo.json"
)
TRAVELER_ID = 10000005


class GIClient(BaseClient):
    def __init__(self) -> None:
        super().__init__()
        self._text_maps: dict[Language, dict[str, str]] = {}
        self._data: dict[str, Any] = {}
        self._data_dir /= "gi"

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
            tg.create_task(self._read_data(self._get_file_path(STARWARD_MW_ITEMS_URL)))

    async def download_data_tables(self, *, force: bool = False) -> None:
        await self._download_files(
            [
                *(DATA_URL / f"{file_name}.json" for file_name in DATA_FILE_NAMES),
                STARWARD_MW_ITEMS_URL,
            ],
            force=force,
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
        data: list[dict[str, Any]] = self._data["AvatarExcelConfigData"]
        skill_depots: dict[int, dict[str, Any]] = {
            depot["id"]: depot for depot in self._data["AvatarSkillDepotExcelConfigData"]
        }
        skills: dict[int, dict[str, Any]] = {
            skill["id"]: skill for skill in self._data["AvatarSkillExcelConfigData"]
        }
        costumes = [
            models.CharacterCostume.model_validate(costume)
            for costume in self._data["AvatarCostumeExcelConfigData"]
            if not costume.get("isDefault")
        ]

        for item in data:
            if item.get("useType") != "AVATAR_FORMAL":
                continue

            character = models.Character.model_validate(item)
            character.name = self.translate(character.name, lang=lang)
            character.costumes = [
                costume for costume in costumes if costume.character_id == character.id
            ]
            for costume in character.costumes:
                costume.name = self.translate(costume.name, lang=lang)

            depot = skill_depots.get(item.get("skillDepotId", 0), {})
            energy_skill = skills.get(depot.get("energySkill", 0), {})
            element = energy_skill.get("costElemType")
            if element is not None and element != "None":
                character.element = models.Element(element)

            result.append(character)

        return result

    def get_traveler_elements(self) -> list[models.Element]:
        """Get the elements the Traveler can currently switch to.

        Derived from the Traveler's candidate skill depots: a depot with an energy
        skill corresponds to a released element.
        """
        data: list[dict[str, Any]] = self._data["AvatarExcelConfigData"]
        skill_depots: dict[int, dict[str, Any]] = {
            depot["id"]: depot for depot in self._data["AvatarSkillDepotExcelConfigData"]
        }
        skills: dict[int, dict[str, Any]] = {
            skill["id"]: skill for skill in self._data["AvatarSkillExcelConfigData"]
        }

        traveler = next(item for item in data if item["id"] == TRAVELER_ID)
        elements: list[models.Element] = []
        for depot_id in traveler.get("candSkillDepotIds", []):
            depot = skill_depots.get(depot_id, {})
            energy_skill = skills.get(depot.get("energySkill", 0), {})
            element = energy_skill.get("costElemType")
            if element is not None and element != "None":
                elements.append(models.Element(element))

        return elements

    def _get_mw_costume_icons(self) -> tuple[dict[int, str], dict[int, str]]:
        """Get the icon names of MW costumes and costume suits.

        The costume table only has icon hashes; the materials that grant a costume or a
        costume suit have the icon names.

        Returns:
            Maps of costume ID to icon name and suit ID to icon name.
        """
        materials: list[dict[str, Any]] = self._data["BydMaterialExcelConfigData"]
        costume_icons: dict[int, str] = {}
        suit_icons: dict[int, str] = {}
        for material in materials:
            for use in material.get("itemUse", []):
                if use.get("useOp") == "BYD_MATERIAL_USE_GAIN_COSTUME":
                    costume_icons[int(use["useParam"][0])] = material["icon"]
                elif use.get("useOp") in {
                    "BYD_MATERIAL_USE_GAIN_COSTUME_SUIT",
                    "BYD_MATERIAL_USE_GAIN_TRIAL_COSTUME_SUIT",
                }:
                    suit_icons[int(use["useParam"][0])] = material["icon"]
        return costume_icons, suit_icons

    def get_mw_costumes(self, *, lang: Language = Language.EN) -> list[models.MWCostume]:
        result: list[models.MWCostume] = []
        data: list[dict[str, Any]] = self._data["BeyondCostumeExcelConfigData"]
        costume_icons, suit_icons = self._get_mw_costume_icons()

        for item in data:
            try:
                costume = models.MWCostume.model_validate(item)
            except ValidationError as e:
                logger.warning("Failed to validate MW costume: {}", e)
                continue
            costume.name = self.translate(costume.name, lang=lang)
            # Suit pieces fall back to their suit's icon
            icon = costume_icons.get(costume.id) or suit_icons.get(item.get("suitId", 0))
            if icon is not None:
                costume.icon = f"https://static.nanoka.cc/assets/gi/{icon}.webp"
            result.append(costume)
        return result

    def _get_mw_item_fallback_icons(self) -> dict[int, str]:
        """Get the icon names of MW items that have no icon of their own.

        Catalogs use the icon of the costume or suit they unlock, emojis derive theirs from
        the emoji prefab name, and poses come from the Starward data.

        Returns:
            A map of item ID to icon name.
        """
        materials: list[dict[str, Any]] = self._data["BydMaterialExcelConfigData"]
        costume_icons, suit_icons = self._get_mw_costume_icons()
        costume_suits: dict[int, int] = {
            costume["costumeId"]: costume.get("suitId", 0)
            for costume in self._data["BeyondCostumeExcelConfigData"]
        }
        drawing_deob = deob.BeyondCostumeDrawingDeobfuscator(
            {"data": self._data["BeyondCostumeDrawingExcelConfigData"]}
        )
        drawings: dict[int, list[int]] = {
            drawing["id"]: drawing["costumeIds"] for drawing in drawing_deob.deobfuscate()
        }
        emoji_prefabs: dict[int, str] = {
            emoji["id"]: emoji["prefabName"] for emoji in self._data["BeyondEmojiExcelConfigData"]
        }
        starward_icons: dict[int, str] = {
            item["Id"]: URL(item["Icon"]).name.removesuffix(".png")
            for item in self._data["GenshinBeyondGachaInfo"]
            if item.get("Icon")
        }

        icons: dict[int, str] = {}
        for material in materials:
            for use in material.get("itemUse", []):
                icon: str | None = None
                if use.get("useOp") == "BYD_MATERIAL_USE_GAIN_COSTUME_DRAWING":
                    # Suit catalogs unlock a girl and a boy suit; use the first one's icon
                    costume_id = drawings.get(int(use["useParam"][0]), [0])[0]
                    icon = (
                        costume_icons.get(costume_id)
                        or suit_icons.get(costume_id)
                        or suit_icons.get(costume_suits.get(costume_id, 0))
                    )
                elif use.get("useOp") == "BYD_MATERIAL_USE_GAIN_EMOJI":
                    prefab = emoji_prefabs.get(int(use["useParam"][0]))
                    if prefab is not None:
                        name = prefab.removeprefix("Beyd_Eff_UI_Emoji_").removeprefix("Common_")
                        icon = f"UI_UGC_Emoji_{name}"
                elif use.get("useOp") == "BYD_MATERIAL_USE_GAIN_POSE":
                    icon = starward_icons.get(material["id"])
                if icon:
                    icons[material["id"]] = icon
        return icons

    def get_mw_items(self, *, lang: Language = Language.EN) -> list[models.MWItem]:
        result: list[models.MWItem] = []
        data: list[dict[str, Any]] = self._data["BydMaterialExcelConfigData"]
        fallback_icons = self._get_mw_item_fallback_icons()
        for item in data:
            try:
                mw_item = models.MWItem.model_validate(item)
            except ValidationError as e:
                logger.warning("Failed to validate MW item: {}", e)
                continue
            mw_item.name = self.translate(mw_item.name, lang=lang)
            mw_item.description = self.translate(mw_item.description, lang=lang)
            if mw_item.icon is None and (icon := fallback_icons.get(mw_item.id)) is not None:
                mw_item.icon = f"https://static.nanoka.cc/assets/gi/{icon}.webp"
            result.append(mw_item)
        return result
