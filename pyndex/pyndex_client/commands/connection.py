import click
from ..util import AliasedGroup
from ..models import AppContext, ConfigEntry
from ...pyndex_api import Pyndex
import urllib.parse


@click.group(name="connection", invoke_without_command=True, cls=AliasedGroup)
@click.pass_context
def connection(ctx: click.Context):
    """Operate on configured connections & logins."""
    obj: AppContext = ctx.obj

    if ctx.invoked_subcommand == None:
        if obj.client:
            obj.console.print(
                f"[bold]Active Connection:[/] {obj.repo.name} ({obj.repo.host.rstrip('/')}{'/' + obj.repo.base_url.lstrip('/') if obj.repo.base_url else ''})"
            )
            try:
                current = obj.client.users.active
            except:
                obj.error("Login failure.")
                raise click.Abort()

            obj.console.print(f"\t[bold]Username:[/] {current.name}")
            obj.console.print(
                f"\t[bold]Groups:[/] {', '.join([i.display_name + ' (' + i.name + ')' for i in current.groups])}"
            )
        else:
            obj.console.print("[bold]Active Connection:[/] None")


@connection.command("add")
@click.argument("host")
@click.option("--name", "-n", "name", help="Connection name (optional)")
@click.option(
    "--base-url", "-b", "base_url", help="Base API URL (optional)", default=""
)
@click.option("--username", "-u", "username", help="Username for connection (optional)")
@click.option("--password", "-p", "password", help="Password for connection (optional)")
@click.pass_obj
def add_connection(
    obj: AppContext,
    host: str,
    name: str | None,
    base_url: str | None,
    username: str | None,
    password: str | None,
):
    """Add a connection to HOST with optional parameters."""
    if not name:
        name = urllib.parse.urlparse(host).hostname

    with Pyndex(
        host, api_base=base_url, username=username, password=password
    ).session() as index:
        try:
            active = index.users.active
        except:
            obj.error("Failed to authenticate against specified connection.")
            raise click.Abort()
    new_entry = ConfigEntry(
        name=name, host=host, base_url=base_url, username=username, password=password
    )
    obj.config.repositories[new_entry.name] = new_entry
    if not obj.config.default:
        obj.config.default = new_entry.name

    obj.console.print(f"[bold green]Connected:[/bold green] {active.name} @ {host}")


@connection.command("default")
@click.argument("name")
@click.pass_obj
def set_default_connection(obj: AppContext, name: str):
    """Sets the default connection to NAME"""
    if name in obj.config.repositories.keys():
        obj.config.default = name
        obj.console.print(
            f"Set active connection to {name} ({obj.config.repositories[name].host})"
        )
    else:
        obj.error(f"Unknown connection {name}")
        raise click.Abort()


@connection.command("list")
@click.pass_obj
def list_connections(obj: AppContext):
    """List configured connections"""
    obj.console.print("[bold]Configured Connections:")
    for conn in obj.config.repositories.values():
        obj.console.print(
            f"[bold]* {conn.name}{' - ACTIVE' if conn.name == obj.config.default else ''}"
        )
        obj.console.print(f"\t[bold]Host:[/bold] {conn.host}")
        obj.console.print(
            f"\t[bold]Username:[/bold] {conn.username if conn.username else 'None'}"
        )


@connection.command("remove")
@click.argument("name")
@click.pass_obj
def remove_connection(obj: AppContext, name: str):
    """Remove connection NAME"""
    if name in obj.config.repositories.keys():
        to_remove = obj.config.repositories[name]
        if obj.config.default == name:
            obj.config.default = None

        del obj.config.repositories[name]
        obj.console.print(f"Removed connection {name}")
    else:
        obj.error(f"Unknown connection {name}")
        raise click.Abort()
