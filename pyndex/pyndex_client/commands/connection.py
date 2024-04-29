import click
from ..models import *
from pyndex.common import Pyndex
import urllib.parse


@click.group("connection", invoke_without_command=True)
@click.pass_context
def connection(ctx: click.Context):
    """Contains commands pertaining to the active connection. When invoked alone, prints out information about the currently active connection."""
    if ctx.invoked_subcommand == None:
        context: Context = ctx.obj
        if context.repo:
            context.console.print(
                f"[green][bold]Active Connection:[/bold] {context.repo.name} @ {context.repo.url}"
            )

            with context.index() as index:
                if index.user:
                    context.console.print(
                        f"[green][bold]Active User:[/bold] {index.user.name if index.user.name else 'anonymous'}"
                    )
                else:
                    context.console.print(
                        f"[red][bold]Error:[/bold] Attempt to login to {context.repo.name} as {context.repo.username} failed"
                    )
        else:
            context.console.print(f"[red]No active connection.")


@connection.command("add")
@click.argument("url", type=str)
@click.option(
    "--name",
    "-n",
    "name",
    default=None,
    type=str,
    help="The name to call this connection in the config. If not specified, defaults to the domain name of URL",
)
@click.option(
    "--username",
    "-u",
    "username",
    default=None,
    type=str,
    help="Username for the selected index",
)
@click.option(
    "--password",
    "-p",
    "password",
    default=None,
    type=str,
    help="Password for the selected index",
)
@click.option(
    "--token",
    "-t",
    "token",
    default=None,
    type=str,
    help="API token for the selected index",
)
@click.option(
    "--default/--no-default",
    "default",
    default=False,
    help="Whether to set this index as the default (ignored if no default is currently set)",
)
@click.pass_obj
def add_connection(
    obj: Context,
    url: str,
    name: str | None,
    username: str | None,
    password: str | None,
    token: str | None,
    default: bool,
):
    """
    Adds the Pyndex instance at URL to the local configuration.
    """

    if not name:
        name = urllib.parse.urlparse(url).hostname

    with Pyndex(url, username=username, password=password, token=token) as index:
        user = index.user
        if not user:
            obj.console.print(
                "[red][bold]Error:[/bold] Invalid credentials supplied.[/red]"
            )
            raise click.Abort()

        obj.console.print(f"Connected as {user.name}. Saving connection as {name}...")

    index = PyndexIndex(
        name=name, url=url, username=username, password=password, token=token
    )
    obj.config.index[name] = index
    if default or not obj.config.default:
        obj.config.default = name

    obj.config.save(obj.config_file_path)


@connection.command("rm")
@click.argument("name", type=str)
@click.pass_obj
def remove_connection(obj: Context, name: str):
    """Removes a connection from the local configuration"""

    if not name in obj.config.index.keys():
        obj.console.print("[red][bold]Error:[/bold] Unknown index name[/red]")
        raise click.Abort()

    if obj.config.default == name:
        obj.config.default = None

    del obj.config.index[name]
    obj.config.save(obj.config_file_path)
