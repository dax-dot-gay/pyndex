from typing import Annotated, Any
from litestar import Litestar
from litestar.datastructures import State
from litestar.di import Provide
from .models import CONTEXT, CONFIG
from .config import Config
from .context import Context
from .routes import make_api_router


async def on_start(app: Litestar):
    app.state.context = CONTEXT


async def provide_context(state: State) -> Context:
    return state.context


app = Litestar(
    route_handlers=[make_api_router(CONFIG.api.path_base)],
    state=State({"context": None}),
    dependencies={"context": Provide(provide_context)},
)
