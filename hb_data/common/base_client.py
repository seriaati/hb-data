from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Self

import aiofiles
import aiofiles.os
import aiohttp
import orjson
from loguru import logger

if TYPE_CHECKING:
    from collections.abc import Sequence
    from os import PathLike

    from yarl import URL


class BaseClient:
    def __init__(self) -> None:
        self._session: aiohttp.ClientSession | None = None
        self._data_dir = Path(".hb_data")

    async def __aenter__(self) -> Self:
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:  # noqa: ANN001
        await self.close()

    @property
    def session(self) -> aiohttp.ClientSession:
        if self._session is None:
            msg = "Client session is not initialized. Run `await client.start()` first."
            raise RuntimeError(msg)
        return self._session

    async def start(self) -> None:
        self._session = aiohttp.ClientSession()
        await self._create_data_dir()

    async def close(self) -> None:
        await self.session.close()

    async def _create_data_dir(self) -> None:
        if not await aiofiles.os.path.exists(self._data_dir):
            await aiofiles.os.mkdir(self._data_dir)

            # Create .gitignore file with *
            gitignore_path = self._data_dir / ".gitignore"
            async with aiofiles.open(gitignore_path, "w") as f:
                await f.write("*\n")

    def _create_filename_from_url(self, url: URL) -> str:
        return url.parts[-1]

    def _get_file_path(self, url: URL) -> Path:
        return self._data_dir / self._create_filename_from_url(url)

    async def _download_file(self, url: URL, file_path: PathLike) -> None:
        file_path = Path(file_path)
        async with self.session.get(url) as resp:
            logger.debug(f"Downloading {url} to {file_path}...")
            resp.raise_for_status()

            _tmp_fd, tmp_path = tempfile.mkstemp(dir=file_path.parent)
            try:
                async with aiofiles.open(file_path, "wb") as f:
                    async for chunk in resp.content.iter_chunked(1024):
                        await f.write(chunk)
                await aiofiles.os.rename(tmp_path, file_path)
            except Exception as e:
                logger.error(f"Failed to download {url}: {e}")
                if await aiofiles.os.path.exists(tmp_path):
                    await aiofiles.os.remove(tmp_path)

    async def _download_files(self, urls: Sequence[URL], *, force: bool = False) -> None:
        async with asyncio.TaskGroup() as tg:
            for url in urls:
                file_path = self._get_file_path(url)
                if not force and await aiofiles.os.path.exists(file_path):
                    logger.debug(f"File {file_path} already exists, skipping download.")
                    continue
                tg.create_task(self._download_file(url, file_path))

    async def _read_json(self, file_path: PathLike) -> dict:
        try:
            async with aiofiles.open(file_path, "rb") as f:
                content = await f.read()
            return orjson.loads(content)
        except FileNotFoundError:
            logger.warning(f"File {file_path} not found. Run `await client.download()` first.")
            return {}
        except orjson.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from {file_path}: {e}")
            return {}
