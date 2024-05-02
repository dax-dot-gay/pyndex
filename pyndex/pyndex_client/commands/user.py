from ..util import AliasResolver
from ..models import Context
from pyndex.common import ApiError
import click


@click.group("user", invoke_without_command=True, cls=AliasResolver)
@click.pass_context
def user(ctx: click.Context):
    """Perform operations on users. When invoked alone, prints information about the current user."""
    context: Context = ctx.obj
    if not context.repo:
        context.console.print("[red]No active connection.[/red]")
        raise click.Abort()

    if ctx.invoked_subcommand == None:
        with context.index() as index:
            result = index.user
            if result == None:
                context.console.print(
                    f"[red][bold]Error:[/bold] Failed to login as {context.repo.username} to {context.repo.url}.[/red]"
                )
                raise click.Abort()

            context.console.print(
                f"[green][bold]Success:[/bold] Logged in to {context.repo.url}."
            )
            context.console.print(
                f"[green][bold]Auth Type:[/bold][/green]\t{result.type}"
            )
            context.console.print(f"[green][bold]User:[/bold][/green]\t\t{result.name}")
            context.console.print(
                f"[green][bold]Groups:[/bold][/green]\t\t{', '.join([(i.display_name + '(' + i.name + ')') if i.display_name else i for i in result.groups])}"
            )


@user.command("create")
@click.option(
    "--username", "-u", "username", prompt="Username", help="Username for the new user"
)
@click.option(
    "--password",
    "-p",
    "password",
    prompt="Password",
    hide_input=True,
    confirmation_prompt=True,
    prompt_required=False,
    help="Password for the new user. If left blank, no password will be set.",
)
@click.pass_context
def create_user(ctx: click.Context, username: str, password: str | None):
    """
    Creates a new user with a username & optional password. Can only be executed if the current user has the `meta.admin` permission.
    """
    context: Context = ctx.obj
    with context.index() as index:
        if not index.admin:
            context.console.print(
                "[bold red]Error:[/bold red]\t Active user does not have the `meta.admin` permission for this connection."
            )
            raise click.Abort()

        try:
            result = index.create_user(username, password=password)
        except ApiError as e:
            context.console.print(f"[bold red]API Error:[/bold red]\t {e.reason}")
            raise click.Abort()

        context.console.print(
            f"[bold green]Success:[/bold green]\tCreated user {result.name}."
        )


@user.command("list")
@click.pass_obj
def list_users(obj: Context):
    with obj.index() as index:
        try:
            result = index.get_users()
        except ApiError as e:
            obj.console.print(f"[bold red]API Error:[/bold red]\t {e.reason}")
            raise click.Abort()

        obj.console.print(f"[bold green]Existing Users:[/bold green]\n")
        for user in result:
            obj.console.print(
                f"  - {user.name}{' (Active)' if user.id == index.user.id else ''}"
            )
            obj.console.print(
                f"    [bold]Groups:[/bold] {', '.join([(i.display_name + '(' + i.name + ')') if i.display_name else i for i in user.groups])}\n"
            )


@user.group("modify", cls=AliasResolver)
@click.option(
    "--username", "-u", "username", prompt="Username", help="Username to modify"
)
@click.pass_context
def modify_user(ctx: click.Context, username: str = None):
    pass


@modify_user.command("groupadd")
@click.option(
    "--group",
    "-g",
    "group",
    multiple=True,
    help="The name of a group to add this user to. Can be specified multiple times.",
)
@click.pass_context
def add_groups(ctx: click.Context, group: list[str]):
    username = ctx.parent.params["username"]
    context: Context = ctx.obj
    with context.index() as index:
        if not index.admin:
            context.console.print(
                "[bold red]Error:[/bold red]\t Active user does not have the `meta.admin` permission for this connection."
            )
            raise click.Abort()
        try:
            index.add_user_to_groups(username, group)
        except ValueError:
            context.console.print(f"[bold red]Error:[/bold red]\t Unknown username")
            raise click.Abort()
        except ApiError as e:
            context.console.print(f"[bold red]API Error:[/bold red]\t {e.reason}")
            raise click.Abort()

        context.console.print(
            f"[green bold]Success:[/bold green] Added {len(group)} group(s) to {username}."
        )
