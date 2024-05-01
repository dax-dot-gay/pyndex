from ..util import AliasResolver
from ..models import Context
from pyndex.common import ApiError
import click


@click.group("group", invoke_without_command=True, cls=AliasResolver)
@click.pass_context
def group(ctx: click.Context):
    pass


@group.command("create")
@click.argument("name")
@click.option(
    "--display", "-d", "display_name", help="Optional display name for the group."
)
@click.pass_obj
def create_group(obj: Context, name: str, display_name: str | None):
    """
    Creates a new group given NAME and an optional display name
    """
    with obj.index() as index:
        if not index.admin:
            obj.console.print(
                "[bold red]Error:[/bold red]\t Active user does not have the `meta.admin` permission for this connection."
            )
            raise click.Abort()

        try:
            result = index.create_group(name, display_name=display_name)
        except ApiError as e:
            obj.console.print(f"[bold red]API Error:[/bold red]\t {e.reason}")
            raise click.Abort()

        obj.console.print(
            f"[bold green]Success:[/bold green]\tCreated group {result.name}."
        )
