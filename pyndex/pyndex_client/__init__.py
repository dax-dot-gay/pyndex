import logging
import os
import click
import platformdirs
from .models import *
from .commands import *
from .util import *

logging.getLogger("httpx").disabled = True


@click.group(invoke_without_command=True, cls=AliasResolver)
@click.option(
    "--config",
    "-c",
    "config",
    default=None,
    type=click.Path(resolve_path=True, dir_okay=False),
    help="Path to an existing config file. Defaults to "
    + os.path.join(platformdirs.user_config_dir(appname="pyndex"), "pyndex.conf"),
)
@click.option(
    "--verbose",
    "-v",
    count=True,
    help="Desired verbosity of output. Can be specified multiple times for increased verbosity (ie -vvv)",
)
@click.option(
    "--repo",
    "-r",
    default=None,
    help="Pyndex instance name to override configured default.",
)
@click.pass_context
def main(ctx: click.Context, config: str | None, verbose: int, repo: str):
    if config:
        config_path = config
    else:
        config_path = os.path.join(
            platformdirs.user_config_dir(appname="pyndex"), "pyndex.conf"
        )

    if not os.path.exists(config_path):
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        PyndexConfig().save(config_path)

    cfg = PyndexConfig.from_file(config_path)
    ctx.obj = Context(
        verbosity=verbose,
        config_file_path=config_path,
        config=cfg,
        repo_override=repo,
        console=rich.console.Console(),
    )


main.add_command(connection)
main.add_command(user)
