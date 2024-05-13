from typing import Literal
import click
from ..util import AliasedGroup
from ..models import AppContext
from ...common import MetaPermission, PackagePermission
from ...pyndex_api.util import ApiError


@click.group("permissions", cls=AliasedGroup, invoke_without_command=True)
@click.pass_context
def perms(ctx: click.Context):
    """View & modify user permissions. If invoked without a command, will list the current user's permissions."""
    if ctx.invoked_subcommand == None:
        obj: AppContext = ctx.obj
        permissions = obj.client.users.active.get_permissions()
        obj.console.print(f"Permissions for [bold]{obj.client.users.active.name}[/]:")
        for perm in permissions:
            if perm.permission in MetaPermission:
                obj.console.print(f"     - SERVER: {perm.permission.split('.')[1]}")
            else:
                obj.console.print(
                    f"     - PACKAGE {perm.project}: {perm.permission.split('.')[1]}"
                )


@perms.command("add")
@click.option(
    "-g",
    "--group",
    "group",
    help="Group name to add permission to (cannot be specified with --user)",
)
@click.option(
    "-u",
    "--user",
    "user",
    help="Username to add permission to (cannot be specified with --group)",
)
@click.option(
    "-p",
    "--permission",
    "permission",
    type=click.Choice(
        ["server:admin", "server:create", "pkg:manage", "pkg:edit", "pkg:view"],
        case_sensitive=False,
    ),
    help="""Which permission to add to the selected user/group:

\b
- server:admin  : Allow all server & package operations.
- server:create : Allow package creation.
- pkg:manage    : Allow administration of a package (--package must be specified)
- pkg:edit      : Allow uploading new versions of a package (--package must be specified)
- pkg:view      : Allow administration of a package (--package must be specified)""",
)
@click.option(
    "-k", "--package", "package", help="Package to add a package permission to."
)
@click.pass_obj
def add_permission(
    obj: AppContext,
    group: str | None,
    user: str | None,
    permission: Literal[
        "server:admin", "server:create", "pkg:manage", "pkg:edit", "pkg:view"
    ],
    package: str | None,
):
    """Add a permission to a user or group. Must also specify a package name if adding permissions for a package."""
    if group and user or (not group and not user):
        obj.error("Exactly one of --user or --group must be provided.")
        raise click.Abort()

    category, perm = permission.split(":")
    target = (
        obj.client.users(username=user) if user else obj.client.groups(group_name=group)
    )
    if not target:
        obj.error(f"Unknown target {target}.")
        raise click.Abort()

    try:
        match category:
            case "server":
                target.add_server_permission("meta." + perm)
            case "pkg":
                if not package:
                    obj.error(
                        "--package must be specified when adding a package permission."
                    )
                    raise click.Abort()

                target.add_package_permission("pkg." + perm, package)
    except ApiError as e:
        obj.error(f"Failed to add {permission} for {target.name}: {e.detail}")
        raise click.Abort()

    obj.console.print(f"[green bold]Success:[/] Added {permission} for {target.name}")


@perms.command("remove")
@click.option(
    "-g",
    "--group",
    "group",
    help="Group name to remove permission from (cannot be specified with --user)",
)
@click.option(
    "-u",
    "--user",
    "user",
    help="Username to remove permission from (cannot be specified with --group)",
)
@click.option(
    "-p",
    "--permission",
    "permission",
    type=click.Choice(
        ["server:admin", "server:create", "pkg:manage", "pkg:edit", "pkg:view"],
        case_sensitive=False,
    ),
    help="""Which permission to remove from the selected user/group:

\b
- server:admin  : Allow all server & package operations.
- server:create : Allow package creation.
- pkg:manage    : Allow administration of a package (--package must be specified)
- pkg:edit      : Allow uploading new versions of a package (--package must be specified)
- pkg:view      : Allow administration of a package (--package must be specified)""",
)
@click.option(
    "-k",
    "--package",
    "package",
    help="Package to remove selected permission on target from.",
)
@click.pass_obj
def remove_permission(
    obj: AppContext,
    group: str | None,
    user: str | None,
    permission: Literal[
        "server:admin", "server:create", "pkg:manage", "pkg:edit", "pkg:view"
    ],
    package: str | None,
):
    """Remove a permission from a user or group. Must also specify a package name if removing permissions for a package."""
    if group and user or (not group and not user):
        obj.error("Exactly one of --user or --group must be provided.")
        raise click.Abort()

    category, perm = permission.split(":")
    target = (
        obj.client.users(username=user) if user else obj.client.groups(group_name=group)
    )
    if not target:
        obj.error(f"Unknown target {target}.")
        raise click.Abort()

    try:
        match category:
            case "server":
                target.delete_server_permission("meta." + perm)
            case "pkg":
                if not package:
                    obj.error(
                        "--package must be specified when removing a package permission."
                    )
                    raise click.Abort()

                target.delete_package_permission("pkg." + perm, package)
    except ApiError as e:
        obj.error(f"Failed to remove {permission} for {target.name}: {e.detail}")
        raise click.Abort()

    obj.console.print(f"[green bold]Success:[/] Removed {permission} for {target.name}")
