import click
from ..util import AliasedGroup
from ..models import AppContext
from ...pyndex_api.util import ApiError


@click.group("group", cls=AliasedGroup)
def group():
    """Manage groups on the connected instance"""
    pass


@group.command("create")
@click.argument("name")
@click.option("-d", "--display", "display", help="Optional display name")
@click.pass_obj
def create_group(obj: AppContext, name: str, display: str | None):
    """Create a new group called NAME"""
    try:
        result = obj.client.groups.create(name, display_name=display)
    except ApiError as e:
        obj.error("Group creation failed - " + e.detail)
        raise click.Abort()

    obj.console.print(f"[bold green]Success:[/] Created group {result.name}")


@group.command("list")
@click.option(
    "--members/--no-members",
    "members",
    default=False,
    help="Whether to list members of each group.",
)
@click.pass_obj
def list_groups(obj: AppContext, members: bool):
    """List all groups on the local index, optionally with a list of members for each."""
    try:
        result = obj.client.groups.all()
        obj.console.print("[bold]Groups:[/]")
        for group in result:
            obj.console.print(
                f"\t* {group.name}{' (' + group.display_name + ')' if group.display_name else ''}"
            )
            if members:
                group_members = group.get_members()
                obj.console.print(
                    f"\t  Members: {', '.join([i.name for i in group_members]) if len(group_members) > 0 else '-'}"
                )
    except ApiError as e:
        obj.error("Group listing failed - " + e.detail)
        raise click.Abort()


@group.command("add-members")
@click.argument("group")
@click.option(
    "-u", "--user", "users", multiple=True, help="Username(s) to add to GROUP"
)
@click.pass_obj
def add_members(obj: AppContext, group: str, users: tuple[str]):
    """Add member(s) to GROUP"""
    try:
        group_result = obj.client.groups(group_name=group)
        if not group_result:
            obj.error(f"Unknown group {group}")
            raise click.Abort()
        c = 1
        for user in users:
            user_result = obj.client.users(username=user)
            if user_result:
                group_result.add_member(user_result)
                obj.console.print(f" - Added member {user} - {c}/{len(users)}")
            else:
                obj.console.print(
                    f"[orange]Warning:[/] Failed adding user [bold]{user}[/] - {c}/{len(users)}"
                )

            c += 1

    except ApiError as e:
        obj.error("Adding members failed - " + e.detail)
        raise click.Abort()


@group.command("remove-members")
@click.argument("group")
@click.option(
    "-u", "--user", "users", multiple=True, help="Username(s) to remove from GROUP"
)
@click.pass_obj
def remove_members(obj: AppContext, group: str, users: tuple[str]):
    """Remove member(s) to GROUP"""
    try:
        group_result = obj.client.groups(group_name=group)
        if not group_result:
            obj.error(f"Unknown group {group}")
            raise click.Abort()
        c = 1
        for user in users:
            user_result = obj.client.users(username=user)
            if user_result:
                group_result.delete_member(user_result)
                obj.console.print(
                    f" - Removed member [bold]{user}[/] - {c}/{len(users)}"
                )
            else:
                obj.console.print(
                    f"[orange]Warning:[/] Failed removing user [bold]{user}[/] - {c}/{len(users)}"
                )

            c += 1

    except ApiError as e:
        obj.error("Adding members failed - " + e.detail)
        raise click.Abort()
