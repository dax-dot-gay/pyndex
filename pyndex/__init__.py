import logging

logger = logging.getLogger(name="pyndex")
logger.setLevel(logging.WARNING)

FEATURES = []

try:
    from .pyndex_server import app as server

    FEATURES.append("server")
except ImportError:
    raise

from .common import *
from .pyndex_api import Pyndex
from .version import *
