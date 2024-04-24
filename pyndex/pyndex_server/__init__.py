from traceback import print_exc
from typing import Annotated, Any
from litestar import Litestar
from litestar.datastructures import State
from litestar import MediaType, Request, Response
from litestar.exceptions import HTTPException
from litestar.status_codes import HTTP_500_INTERNAL_SERVER_ERROR
from litestar.di import Provide
from .config import Config
from .context import Context
from .routes import make_api_router

CONFIG = Config.load()
CONTEXT = Context(CONFIG)


async def on_start(app: Litestar):
    app.state.context = CONTEXT


async def provide_context(state: State) -> Context:
    return state.context


def plain_text_exception_handler(_: Request, exc: Exception) -> Response:
    """Default handler for exceptions subclassed from HTTPException."""
    status_code = getattr(exc, "status_code", HTTP_500_INTERNAL_SERVER_ERROR)
    detail = getattr(exc, "detail", "")
    print_exc()

    return Response(
        media_type=MediaType.TEXT,
        content=detail,
        status_code=status_code,
    )


app = Litestar(
    route_handlers=[make_api_router(CONFIG.api.path_base)],
    state=State(),
    dependencies={"context": Provide(provide_context)},
    exception_handlers={HTTP_500_INTERNAL_SERVER_ERROR: plain_text_exception_handler},
    on_startup=[on_start],
)
