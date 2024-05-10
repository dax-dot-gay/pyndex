import click
from ..util import AliasedGroup
from ..models import AppContext
from ...common import MetaPermission, PackagePermission
from rich.markdown import Markdown
from ...pyndex_api.util import ApiError


@click.group("user", cls=AliasedGroup)
def user():
    """Commands related to user management."""
    pass


@user.command("create")
@click.option("--username", "-u", "username", help="Username of user to create.")
@click.option("--password", "-p", "password", help="Optional password to set")
@click.pass_obj
def create_user(obj: AppContext, username: str, password: str | None):
    """Creates a new user with a username & optional password. Requires admin permissions."""
    if not username:
        obj.error("A username is required.")
        raise click.Abort()

    try:
        result = obj.client.users.create(username, password=password)
    except ApiError as e:
        obj.error(f"Failed to create user: {e.detail}")
        raise click.Abort()

    obj.console.print(f"[bold]Success: [/bold]Created user {result.name}")


@user.command("list")
@click.option(
    "--permissions", is_flag=True, help="Whether to display user permissions."
)
@click.pass_obj
def list_users(obj: AppContext, permissions: bool):
    """Lists all users on the current index."""
    users = obj.client.users.all()
    obj.console.print("[bold]Users:[/]")
    for user in users:
        obj.console.print(f"  * {user.name}")
        obj.console.print(
            f"    [italic]Groups: [/]{', '.join([group.name + (' ('+group.display_name+')' if group.display_name else '') for group in user.groups]) if len(user.groups) > 0 else '-'}"
        )
        if permissions:
            perms = user.get_permissions()
            if len(perms) > 0:
                obj.console.print("    [italic]Permissions: [/]")
                for perm in perms:
                    if perm.permission in MetaPermission:
                        obj.console.print(
                            f"     - SERVER: {perm.permission.split('.')[1]}"
                        )
                    else:
                        obj.console.print(
                            f"     - PACKAGE {perm.project}: {perm.permission.split('.')[1]}"
                        )
            else:
                obj.console.print("    [italic]Permissions: [/] -")


@user.command("delete")
@click.argument("username")
@click.pass_obj
def delete_user(obj: AppContext, username: str):
    """Deletes a user by USERNAME"""
    try:
        user = obj.client.users(username=username)
        if user == None:
            obj.error(f"Unknown user {username}")
            raise click.Abort()

        user.delete()
        obj.console.print(f"Deleted user {username}.")
    except ApiError as e:
        obj.error(f"Failed to delete user: {e.detail}")
