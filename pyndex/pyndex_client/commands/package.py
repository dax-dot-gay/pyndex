from email.policy import default
import click
from ..util import AliasedGroup
from ..models import AppContext
from rich.markdown import Markdown


@click.group("package", cls=AliasedGroup)
def package():
    """Operate on individual or aggregate packages."""
    pass


@package.command("list")
@click.pass_obj
def list_packages(obj: AppContext):
    """List all packages accessible to the logged-in user."""
    obj.console.print("[bold]Repositories:[/]")
    for package in obj.client.package.all():
        obj.console.print(
            f"\t* [bold]{package.info.name} - {package.info.version}[/]\n"
        )
        obj.console.print(f"\t  [underline]Summary[/]  : {package.info.summary}")
        obj.console.print(f"\t  [underline]Authors[/]  : {package.info.author_email}")
        obj.console.print(
            f"\t  [underline]Keywords[/] : {', '.join([i.strip() for i in package.info.keywords.split(',')]) if package.info.keywords else '-'}"
        )


@package.command("show")
@click.argument("name")
@click.option(
    "--version", "-v", "version", help="Optional version to get information about."
)
@click.option(
    "--local",
    "-l",
    "local",
    is_flag=True,
    help="Whether to only retrieve results from the local index.",
)
@click.option(
    "--describe/--no-describe",
    "describe",
    default=True,
    help="Whether to include full text of markdown description.",
)
@click.pass_obj
def show_package(
    obj: AppContext, name: str, version: str | None, local: bool, describe: bool
):
    """Show detailed information about a specific package by NAME"""

    package = obj.client.package(name, version=version, local=local)
    if package:
        obj.console.print(
            f"[bold]Found {'Local' if package.local else 'Remote'} Package:[/] {package.info.name} v{package.info.version}"
        )
        obj.console.print(f"\t  [underline]Summary[/]        : {package.info.summary}")
        obj.console.print(
            f"\t  [underline]Authors[/]        : {package.info.author_email}"
        )
        obj.console.print(
            f"\t  [underline]Python Version[/] : {package.info.requires_python if package.info.requires_python else '-'}"
        )
        obj.console.print(
            f"\t  [underline]Keywords[/]       : {', '.join([i.strip() for i in package.info.keywords.split(',')]) if package.info.keywords else '-'}"
        )
        obj.console.print(
            f"\t  [underline]Classifiers[/]    : {'\n\n\t    * ' + '\n\t    * '.join(package.info.classifiers) if package.info.classifiers else '-'}"
        )
        if describe:
            obj.console.print(
                f"\t  [underline]Description[/]    : {'\n' if package.info.description else '-'}"
            )
            if package.info.description:
                obj.console.print(Markdown(package.info.description))

    else:
        obj.error("Failed to resolve package.")
