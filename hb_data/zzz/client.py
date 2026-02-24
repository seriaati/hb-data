from __future__ import annotations

import asyncio
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Self

from loguru import logger
from pydantic import ValidationError
from yarl import URL

from hb_data.common.base_client import BaseClient
from hb_data.common.dict_utils import merge_dicts_by_different_keys, merge_dicts_by_key
from hb_data.zzz import deob, models

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path


class Language(StrEnum):
    CHT = "CHT"
    CHS = "CHS"
    DE = "DE"
    EN = "EN"
    ES = "ES"
    FR = "FR"
    ID = "ID"
    JA = "JA"
    KO = "KO"
    PT = "PT"
    RU = "RU"
    TH = "TH"
    VI = "VI"


BASE_URL = URL("https://git.mero.moe/dimbreath/ZenlessData/raw/branch/master")
TEXT_MAP_URL = BASE_URL / "TextMap"
DATA_URL = BASE_URL / "FileCfg"
DATA_FILE_NAMES = (
    "AvatarBaseTemplateTb",  # Characters
    "AvatarBattleTemplateTb",  # Character battle properties
    "AvatarUITemplateTb",  # Character properties in UI
    "AvatarSkinBaseTemplateTb",  # Character skins
    "WeaponTemplateTb",  # Weapons
    "ItemTemplateTb",  # Items
    "EquipmentTemplateTb",  # Drive discs
    "EquipmentSuitTemplateTb",  # Drive disc sets
    "BuddyBaseTemplateTb",  # Bangboos
)


class ZZZClient(BaseClient):
    def __init__(self) -> None:
        super().__init__()
        self._text_maps: dict[Language, dict[str, str]] = {}
        self._data: dict[str, Any] = {}
        self._data_dir /= "zzz"

    async def __aenter__(self) -> Self:
        await super().__aenter__()
        await self.download()
        return self

    def _get_text_map_file_name(self, lang: Language) -> str:
        if lang is Language.CHS:
            return "TextMapTemplateTb.json"
        return f"TextMap_{lang.value}TemplateTb.json"

    def _get_text_map_file_names(self, *, langs: Iterable[Language] | None = None) -> list[str]:
        file_names = []
        for lang in Language:
            if langs is not None and lang not in langs:
                continue
            file_names.append(self._get_text_map_file_name(lang))
        return file_names

    async def _read_text_map(self, lang: Language) -> None:
        logger.debug(f"Reading text map for language: {lang}")
        file_name = self._get_text_map_file_name(lang)
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

    def get_characters(self, *, lang: Language = Language.EN) -> list[models.Character]:
        result: list[models.Character] = []

        d_avatar_base = deob.AvatarBaseTemplateTbDeobfuscator(self._data["AvatarBaseTemplateTb"])
        avatar_base = d_avatar_base.deobfuscate()

        d_avatar_battle = deob.AvatarBattleTemplateTbDeobfuscator(
            self._data["AvatarBattleTemplateTb"]
        )
        avatar_battle = d_avatar_battle.deobfuscate()

        d_avatar_ui = deob.AvatarUITemplateTbDeobfuscator(self._data["AvatarUITemplateTb"])
        avatar_ui = d_avatar_ui.deobfuscate()

        d_item = deob.ItemTemplateTbDeobfuscator(self._data["ItemTemplateTb"])
        item_data = d_item.deobfuscate()

        avatar_base = merge_dicts_by_key([avatar_base, avatar_battle, avatar_ui], key="ID")
        avatar_base = merge_dicts_by_different_keys({"ID": avatar_base, "ItemID": item_data})

        d_skin = deob.AvatarSkinBaseTemplateTbDeobfuscator(self._data["AvatarSkinBaseTemplateTb"])
        skin_data = d_skin.deobfuscate()
        skins = [models.CharacterSkin.model_validate(skin) for skin in skin_data]

        for item in avatar_base:
            try:
                character = models.Character.model_validate(item)
            except ValidationError:
                continue

            character.name = self.translate(character.name, lang=lang)
            character.full_name = self.translate(character.full_name, lang=lang)
            character.faction_name = self.translate(character.faction_name, lang=lang)
            character.skins = [
                skin
                for skin in skins
                if skin.character_id == character.id and "DefaultSkin" not in skin.tags
            ]
            result.append(character)

        return result

    def get_weapons(self, *, lang: Language = Language.EN) -> list[models.Weapon]:
        result: list[models.Weapon] = []

        d_weapon = deob.WeaponTemplateTbDeobfuscator(self._data["WeaponTemplateTb"])
        weapon_data = d_weapon.deobfuscate()
        d_item = deob.ItemTemplateTbDeobfuscator(self._data["ItemTemplateTb"])
        item_data = d_item.deobfuscate()
        weapon_data = merge_dicts_by_key([weapon_data, item_data], key="ItemID")

        for item in weapon_data:
            try:
                weapon = models.Weapon.model_validate(item)
            except ValidationError:
                continue

            weapon.name = self.translate(weapon.name, lang=lang)
            result.append(weapon)

        return result

    def get_drive_discs(self, *, lang: Language = Language.EN) -> list[models.DriveDisc]:  # noqa: ARG002
        result: list[models.DriveDisc] = []
        d_equipment = deob.EquipmentTemplateTbDeobfuscator(self._data["EquipmentTemplateTb"])
        equipment_data = d_equipment.deobfuscate()

        for item in equipment_data:
            try:
                drive_disc = models.DriveDisc.model_validate(item)
            except ValidationError:
                continue

            result.append(drive_disc)

        return result

    def get_drive_disc_sets(self, *, lang: Language = Language.EN) -> list[models.DriveDiscSet]:
        result: list[models.DriveDiscSet] = []
        d_suit = deob.EquipmentSuitTemplateTbDeobfuscator(self._data["EquipmentSuitTemplateTb"])
        suit_data = d_suit.deobfuscate()

        for item in suit_data:
            try:
                drive_disc_set = models.DriveDiscSet.model_validate(item)
            except ValidationError:
                continue

            drive_disc_set.name = self.translate(drive_disc_set.name, lang=lang)
            drive_disc_set.two_set_effect = self.translate(drive_disc_set.two_set_effect, lang=lang)
            drive_disc_set.four_set_effect = self.translate(
                drive_disc_set.four_set_effect, lang=lang
            )
            drive_disc_set.story = self.translate(drive_disc_set.story, lang=lang)
            result.append(drive_disc_set)

        return result

    def get_bangboos(self, *, lang: Language = Language.EN) -> list[models.Bangboo]:
        result: list[models.Bangboo] = []
        d_buddy = deob.BuddyBaseTemplateTbDeobfuscator(self._data["BuddyBaseTemplateTb"])
        buddy_data = d_buddy.deobfuscate()

        d_item = deob.ItemTemplateTbDeobfuscator(self._data["ItemTemplateTb"])
        item_data = d_item.deobfuscate()
        buddy_data = merge_dicts_by_different_keys({"ID": buddy_data, "ItemID": item_data})

        for item in buddy_data:
            try:
                bangboo = models.Bangboo.model_validate(item)
            except ValidationError:
                continue

            bangboo.name = self.translate(bangboo.name, lang=lang)
            result.append(bangboo)

        return result

    def get_rarity_map(self) -> dict[int, int]:
        characters = self.get_characters()
        bangboos = self.get_bangboos()
        weapons = self.get_weapons()

        items = characters + bangboos + weapons
        return {item.id: item.rarity for item in items}
