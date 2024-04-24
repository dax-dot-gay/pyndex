from ..context import Context
from ..config import Config

CONFIG: Config = Config.load()
CONTEXT: Context = Context(CONFIG)
