from loguru import logger as _logger

from . import gi, zzz
from .gi import GIClient
from .zzz import ZZZClient

_logger.disable("hb_data")  # noqa: RUF067
