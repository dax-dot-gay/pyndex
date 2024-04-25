FEATURES = ["base"]

try:
    from .pyndex_server import app as server

    FEATURES.append("server")
except ImportError:
    raise

from .pyndex_api import PynDex
