import logging

logger = logging.getLogger(name="pyndex")
logger.setLevel(logging.WARNING)

FEATURES = []

try:
    from .pyndex_server import app as server

    FEATURES.append("server")
except ImportError:
    raise

try:
    from .pyndex_client import main

    FEATURES.append("client")
except ImportError:
    raise

from .common import *
