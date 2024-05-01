from ..util import AliasResolver
from ..models import Context
import click


@click.group("user", invoke_without_command=True, cls=AliasResolver)
@click.pass_context
def user(ctx: click.Context):
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
