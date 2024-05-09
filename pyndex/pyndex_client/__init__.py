import os
import click
import platformdirs
from .models import AppContext
from ..version import *
from .util import AliasedGroup
from .commands import *
import logging

logging.getLogger("httpx").setLevel(logging.CRITICAL)


@click.group(invoke_without_command=True, cls=AliasedGroup)
@click.option(
    "--repo", "-r", "repo", default=None, help="Override of default repository."
)
@click.option(
    "--config",
    "-c",
    "config",
    default=None,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, allow_dash=True),
    help="Override for config file location. Defaults to "
    + os.path.join(platformdirs.user_config_dir(appname="pyndex"), "pyndex.json"),
)
@click.pass_context
def main(ctx: click.Context, repo: str | None, config: str | None):
    ctx.obj = ctx.with_resource(
        AppContext.create(
            (
                config
                if config
                else os.path.join(
                    platformdirs.user_config_dir(appname="pyndex"), "pyndex.json"
                )
            ),
            repository=repo,
        )
    )
    if ctx.invoked_subcommand == None:
        ctx.obj.console.print(f"[bold]Pyndex - v{__version__}")
        ctx.obj.console.print(f"[bold]\tCLI Version:[/] v{__client_version__}")
        ctx.obj.console.print(f"[bold]\tAPI Version:[/] v{__api_version__}")
    else:
        if ctx.invoked_subcommand != "connection" and not ctx.obj.client:
            ctx.obj.error("No connection is configured/active.")

main.add_command(connection)
