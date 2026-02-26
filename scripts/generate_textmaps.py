from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Any

import aiofiles
import orjson
from loguru import logger
from yarl import URL

from hb_data.gi.client import GIClient
from hb_data.gi.client import Language as GILanguage
from hb_data.zzz import deob as zzz_deob
from hb_data.zzz.client import Language as ZZZLanguage
from hb_data.zzz.client import ZZZClient

if TYPE_CHECKING:
    import aiohttp

OUTPUT_DIR = Path("textmaps")

_ZZZ_UPSTREAM_TEXT_MAP_URL = URL(
    "https://git.mero.moe/dimbreath/ZenlessData/raw/branch/master/TextMap"
)
_GI_UPSTREAM_TEXT_MAP_URL = URL("https://gitlab.com/Dimbreath/AnimeGameData/-/raw/master/TextMap")
_GI_HAS_TWO_PARTS = frozenset({GILanguage.RU, GILanguage.TH})


def _extract_zzz_hashes(data: dict[str, Any]) -> set[str]:
    """Extract all text map hash values referenced by ZZZ get_* translation calls."""
    hashes: set[str] = set()

    # get_characters: UIName, FullName from AvatarBaseTemplateTb
    d = zzz_deob.AvatarBaseTemplateTbDeobfuscator(data["AvatarBaseTemplateTb"])
    for entry in d.deobfuscate():
        for field in ("UIName", "FullName"):
            if v := entry.get(field):
                hashes.add(v)

    # get_characters: CampName from AvatarUITemplateTb
    d = zzz_deob.AvatarUITemplateTbDeobfuscator(data["AvatarUITemplateTb"])
    for entry in d.deobfuscate():
        if v := entry.get("CampName"):
            hashes.add(v)

    # get_characters / get_weapons / get_bangboos: Name from ItemTemplateTb
    d = zzz_deob.ItemTemplateTbDeobfuscator(data["ItemTemplateTb"])
    for entry in d.deobfuscate():
        if v := entry.get("Name"):
            hashes.add(v)

    # get_drive_disc_sets: Name, TwoSetEffect, FourSetEffect, SuitStory
    d = zzz_deob.EquipmentSuitTemplateTbDeobfuscator(data["EquipmentSuitTemplateTb"])
    for entry in d.deobfuscate():
        for field in ("Name", "TwoSetEffect", "FourSetEffect", "SuitStory"):
            if v := entry.get(field):
                hashes.add(v)

    return hashes


def _extract_gi_hashes(data: dict[str, Any]) -> set[str]:
    """Extract all text map hash values referenced by GI get_* translation calls.

    GI hashes are stored as integers in the JSON; coerce to str to match the
    text map keys (GI models use coerce_numbers_to_str=True for the same reason).
    """
    hashes: set[str] = set()

    # get_mw_costumes: nameTextMapHash from BeyondCostumeExcelConfigData
    for entry in data.get("BeyondCostumeExcelConfigData", []):
        if v := entry.get("nameTextMapHash"):
            hashes.add(str(v))

    # get_mw_items: nameTextMapHash, descTextMapHash from BydMaterialExcelConfigData
    for entry in data.get("BydMaterialExcelConfigData", []):
        for field in ("nameTextMapHash", "descTextMapHash"):
            if v := entry.get(field):
                hashes.add(str(v))

    return hashes


async def _fetch_json(session: aiohttp.ClientSession, url: URL) -> dict[str, str]:
    async with session.get(url) as resp:
        return orjson.loads(await resp.read())


async def _fetch_zzz_text_maps(session: aiohttp.ClientSession) -> dict[ZZZLanguage, dict[str, str]]:
    def _url(lang: ZZZLanguage) -> URL:
        file_name = (
            "TextMapTemplateTb.json"
            if lang is ZZZLanguage.CHS
            else f"TextMap_{lang.value}TemplateTb.json"
        )
        return _ZZZ_UPSTREAM_TEXT_MAP_URL / file_name

    async def _fetch(lang: ZZZLanguage) -> tuple[ZZZLanguage, dict[str, str]]:
        return lang, await _fetch_json(session, _url(lang))

    return dict(await asyncio.gather(*[_fetch(lang) for lang in ZZZLanguage]))


async def _fetch_gi_text_maps(session: aiohttp.ClientSession) -> dict[GILanguage, dict[str, str]]:
    async def _fetch(lang: GILanguage) -> tuple[GILanguage, dict[str, str]]:
        if lang in _GI_HAS_TWO_PARTS:
            part0, part1 = await asyncio.gather(
                _fetch_json(session, _GI_UPSTREAM_TEXT_MAP_URL / f"TextMap{lang.value}_0.json"),
                _fetch_json(session, _GI_UPSTREAM_TEXT_MAP_URL / f"TextMap{lang.value}_1.json"),
            )
            return lang, {**part0, **part1}
        return lang, await _fetch_json(
            session, _GI_UPSTREAM_TEXT_MAP_URL / f"TextMap{lang.value}.json"
        )

    return dict(await asyncio.gather(*[_fetch(lang) for lang in GILanguage]))


async def _write_json(path: Path, data: dict) -> None:
    await asyncio.to_thread(path.parent.mkdir, parents=True, exist_ok=True)
    async with aiofiles.open(path, "wb") as f:
        await f.write(orjson.dumps(data))


async def generate_zzz(output_dir: Path, *, force: bool) -> None:
    """Download ZZZ data tables and full upstream text maps, strip to needed hashes, write output."""
    client = ZZZClient()
    await client.start()
    try:
        await client.download_data_tables(force=force)
        text_maps = await _fetch_zzz_text_maps(client.session)
        hashes = _extract_zzz_hashes(client._data)
        logger.info(f"ZZZ: {len(hashes)} unique hashes extracted")

        tasks = []
        for lang in ZZZLanguage:
            full_map = text_maps.get(lang, {})
            stripped = {k: v for k, v in full_map.items() if k in hashes}
            file_name = (
                "TextMapTemplateTb.json"
                if lang is ZZZLanguage.CHS
                else f"TextMap_{lang.value}TemplateTb.json"
            )
            logger.info(f"  ZZZ/{lang}: {len(stripped)}/{len(full_map)} entries kept → {file_name}")
            tasks.append(_write_json(output_dir / "zzz" / file_name, stripped))

        await asyncio.gather(*tasks)
    finally:
        await client.close()


async def generate_gi(output_dir: Path, *, force: bool) -> None:
    """Download GI data tables and full upstream text maps, strip to needed hashes, write output.

    RU and TH have split upstream files; we merge them here before stripping.
    We always write a single file per language (TextMapRU.json, TextMapTH.json).
    """
    client = GIClient()
    await client.start()
    try:
        await client.download_data_tables(force=force)
        text_maps = await _fetch_gi_text_maps(client.session)
        hashes = _extract_gi_hashes(client._data)
        logger.info(f"GI: {len(hashes)} unique hashes extracted")

        tasks = []
        for lang in GILanguage:
            full_map = text_maps.get(lang, {})
            stripped = {k: v for k, v in full_map.items() if k in hashes}
            file_name = f"TextMap{lang.value}.json"
            logger.info(f"  GI/{lang}: {len(stripped)}/{len(full_map)} entries kept → {file_name}")
            tasks.append(_write_json(output_dir / "gi" / file_name, stripped))

        await asyncio.gather(*tasks)
    finally:
        await client.close()


async def main(*, force: bool) -> None:
    """Entry point: generate stripped text maps for all games."""
    output_dir = OUTPUT_DIR
    await asyncio.to_thread(output_dir.mkdir, parents=True, exist_ok=True)
    await asyncio.gather(
        generate_zzz(output_dir, force=force), generate_gi(output_dir, force=force)
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download data files even if already cached in .hb_data/",
    )
    args = parser.parse_args()
    asyncio.run(main(force=args.force))
