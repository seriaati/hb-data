from loguru import logger as _logger

from . import gi, hsr, zzz
from .gi import GIClient
from .hsr import HSRClient
from .zzz import ZZZClient

_logger.disable("hb_data")  # ruff: ignore[non-empty-init-module]
