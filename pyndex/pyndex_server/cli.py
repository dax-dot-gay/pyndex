import click
from . import app
from hypercorn.config import Config
from hypercorn.asyncio import serve
import asyncio


@click.command()
@click.option(
    "--bind", "-b", "bind", default="localhost:8000", help="HOST:PORT to bind to"
)
@click.option(
    "--insecure-bind",
    "insecure_bind",
    default=None,
    help="HOST:PORT to bind to insecurely, redirecting to the bind port & HTTPS if TLS is active.",
)
@click.option(
    "--certfile",
    "certfile",
    type=click.Path(exists=True, dir_okay=False),
    help="Certificate file for SSL encryption. If not provided, server will use HTTP.",
)
@click.option(
    "--keyfile",
    "keyfile",
    type=click.Path(exists=True, dir_okay=False),
    help="Private key file for SSL encryption. If not provided, server will use HTTP.",
)
def launch(
    bind: str, insecure_bind: str | None, certfile: str | None, keyfile: str | None
):
    config = Config()
    config.bind = [bind]

    if keyfile and certfile:
        config.keyfile = keyfile
        config.certfile = certfile
        config.insecure_bind = insecure_bind

    asyncio.run(serve(app, config))
