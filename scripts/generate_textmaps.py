from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from typing import Any

import aiofiles
import aiohttp
import orjson
from loguru import logger
from yarl import URL

from hb_data.gi.client import GIClient
from hb_data.gi.client import Language as GILanguage
from hb_data.hsr.client import TRAILBLAZER_NAME_HASH, HSRClient
from hb_data.hsr.client import Language as HSRLanguage
from hb_data.zzz import deob as zzz_deob
from hb_data.zzz.client import Language as ZZZLanguage
from hb_data.zzz.client import ZZZClient

OUTPUT_DIR = Path("textmaps")

_ZZZ_UPSTREAM_TEXT_MAP_URL = URL(
    "https://git.mero.moe/dimbreath/ZenlessData/raw/branch/master/TextMap"
)
_GI_UPSTREAM_TEXT_MAP_URL = URL("https://gitlab.com/Dimbreath/AnimeGameData2/-/raw/main/TextMap")
_GI_HAS_TWO_PARTS = frozenset({GILanguage.RU, GILanguage.TH})
_HSR_UPSTREAM_TEXT_MAP_URL = URL(
    "https://gitlab.com/Dimbreath/turnbasedgamedata/-/raw/main/TextMap"
)
_HSR_HAS_TWO_PARTS = frozenset({HSRLanguage.KR, HSRLanguage.RU, HSRLanguage.TH})


def _extract_zzz_hashes(data: dict[str, Any]) -> set[str]:
    """Extract all text map hash values referenced by ZZZ get_* translation calls."""
    hashes: set[str] = set()

    # get_characters: Name, FullName from AvatarBaseTemplateTb
    d = zzz_deob.AvatarBaseTemplateTbDeobfuscator(data["AvatarBaseTemplateTb"])
    for entry in d.deobfuscate():
        for field in ("Name", "FullName"):
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


def _extract_hsr_hashes(data: dict[str, Any]) -> set[str]:
    """Extract all text map hash values referenced by HSR get_* translation calls."""
    hashes: set[str] = set()

    # get_characters: AvatarName from AvatarConfig
    for entry in data.get("AvatarConfig", []):
        if v := entry.get("AvatarName", {}).get("Hash"):
            hashes.add(str(v))

    return hashes


def _find_hsr_trailblazer_key(text_maps: dict[HSRLanguage, dict[str, str]]) -> str:
    """Locate the upstream text map key for the Trailblazer's name by its EN value.

    The key is re-keyed to the stable TRAILBLAZER_NAME_HASH sentinel when writing
    stripped text maps, so an upstream re-key self-heals on the next generation run.
    """
    en_map = text_maps.get(HSRLanguage.EN, {})
    key = next((k for k, v in en_map.items() if v == "Trailblazer"), None)
    if key is None:
        msg = 'HSR: no key with value "Trailblazer" found in the EN text map'
        raise RuntimeError(msg)
    return key


async def _fetch_json(session: aiohttp.ClientSession, url: URL) -> dict[str, str]:
    async with session.get(url) as resp:
        resp.raise_for_status()
        return orjson.loads(await resp.read())


async def _fetch_zzz_text_maps(session: aiohttp.ClientSession) -> dict[ZZZLanguage, dict[str, str]]:
    async def _fetch(lang: ZZZLanguage) -> tuple[ZZZLanguage, dict[str, str]]:
        def _get_url(overwrite: bool = False) -> URL:
            if lang is ZZZLanguage.CHS:
                stem = "TextMapOverwrite" if overwrite else "TextMap"
            else:
                stem = f"TextMap_{lang.value}Overwrite" if overwrite else f"TextMap_{lang.value}"
            return _ZZZ_UPSTREAM_TEXT_MAP_URL / f"{stem}TemplateTb.json"

        # Fetch the base text map
        base_map = await _fetch_json(session, _get_url())

        # Try to fetch and merge the overwrite text map
        try:
            overwrite_map = await _fetch_json(session, _get_url(overwrite=True))
            base_map.update(overwrite_map)
            logger.info(f"  ZZZ/{lang}: Merged {len(overwrite_map)} overwrite entries")
        except aiohttp.ClientResponseError as e:
            if e.status != 404:
                raise

        return lang, base_map

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


async def _fetch_hsr_text_maps(session: aiohttp.ClientSession) -> dict[HSRLanguage, dict[str, str]]:
    async def _fetch(lang: HSRLanguage) -> tuple[HSRLanguage, dict[str, str]]:
        if lang in _HSR_HAS_TWO_PARTS:
            part0, part1 = await asyncio.gather(
                _fetch_json(session, _HSR_UPSTREAM_TEXT_MAP_URL / f"TextMap{lang.value}_0.json"),
                _fetch_json(session, _HSR_UPSTREAM_TEXT_MAP_URL / f"TextMap{lang.value}_1.json"),
            )
            return lang, {**part0, **part1}
        return lang, await _fetch_json(
            session, _HSR_UPSTREAM_TEXT_MAP_URL / f"TextMap{lang.value}.json"
        )

    return dict(await asyncio.gather(*[_fetch(lang) for lang in HSRLanguage]))


async def _write_json(path: Path, data: dict) -> None:
    await asyncio.to_thread(path.parent.mkdir, parents=True, exist_ok=True)
    async with aiofiles.open(path, "wb") as f:
        await f.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))


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


async def generate_hsr(output_dir: Path, *, force: bool) -> None:
    """Download HSR data tables and full upstream text maps, strip to needed hashes, write output.

    KR, RU, and TH have split upstream files; we merge them here before stripping.
    We always write a single file per language (TextMapKR.json, TextMapRU.json, TextMapTH.json).
    """
    client = HSRClient()
    await client.start()
    try:
        await client.download_data_tables(force=force)
        text_maps = await _fetch_hsr_text_maps(client.session)
        hashes = _extract_hsr_hashes(client._data)
        logger.info(f"HSR: {len(hashes)} unique hashes extracted")

        trailblazer_key = _find_hsr_trailblazer_key(text_maps)
        logger.info(f"HSR: Trailblazer name key located: {trailblazer_key}")

        tasks = []
        for lang in HSRLanguage:
            full_map = text_maps.get(lang, {})
            stripped = {k: v for k, v in full_map.items() if k in hashes}
            if v := full_map.get(trailblazer_key):
                stripped[TRAILBLAZER_NAME_HASH] = v
            file_name = f"TextMap{lang.value}.json"
            logger.info(f"  HSR/{lang}: {len(stripped)}/{len(full_map)} entries kept → {file_name}")
            tasks.append(_write_json(output_dir / "hsr" / file_name, stripped))

        await asyncio.gather(*tasks)
    finally:
        await client.close()


async def main(*, force: bool) -> None:
    """Entry point: generate stripped text maps for all games."""
    output_dir = OUTPUT_DIR
    await asyncio.to_thread(output_dir.mkdir, parents=True, exist_ok=True)
    await asyncio.gather(
        generate_zzz(output_dir, force=force),
        generate_gi(output_dir, force=force),
        generate_hsr(output_dir, force=force),
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
