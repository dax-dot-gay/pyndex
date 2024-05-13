import logging

logger = logging.getLogger(name="pyndex")
logger.setLevel(logging.WARNING)

FEATURES = []

try:
    from .pyndex_server import app as server

    FEATURES.append("server")
except ImportError:
    pass

try:
    from .pyndex_client import main as pyndex_client

    FEATURES.append("client")
except ImportError:
    pass

from .common import *
from .pyndex_api import *
from .version import *
