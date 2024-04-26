import click
from ..models import *
import urllib.parse


@click.group("connection")
@click.pass_obj
def connection(obj: Context):
    pass


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

    index = PyndexIndex(
        name=name, url=url, username=username, password=password, token=token
    )
    obj.config.index[name] = index
    if default or not obj.config.default:
        obj.config.default = name

    obj.config.save(obj.config_file_path)
