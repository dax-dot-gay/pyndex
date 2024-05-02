from tempfile import NamedTemporaryFile
from traceback import print_exc
import rich.columns
from rich.console import RenderResult
import rich.markdown
import rich.padding
import rich.panel
import rich.text
from ..util import AliasResolver
from ..models import Context
from pyndex.common import ApiError
import click
import rich
from rich.text import Text
from rich.layout import Layout
from rich.markdown import Markdown


@click.group("package", cls=AliasResolver)
def package():
    """Contains operations related to packages in the index."""
    pass


@package.command("info")
@click.argument("package")
@click.option("--version", "-v", "version", help="Optional package version to select")
@click.option(
    "--local", "local", is_flag=True, help="Whether to only show local packages"
)
@click.pass_obj
def package_info(
    obj: Context, package: str, version: str | None = None, local: bool = False
):
    """
    Fetches information about PACKAGE, optionally constrained to VERSION. If --local isn't set, will return results from external proxies if the package isn't found locally.
    """
    with obj.index() as index:
        info = index.get_package(package, version=version, allow_proxy=not local)
        if not info:
            obj.console.print(
                f"[bold red]Error:[/bold red] No package matching {package} (version {version if version else 'ANY'}) was found."
            )
            raise click.Abort()

        # Define header components
        header_content = Layout()
        dynamic_height = 0

        # Classifier height check
        class_cols = obj.console.width // max([len(i) for i in info.info.classifiers])
        class_height = len(info.info.classifiers) // class_cols + 2

        header_content.split_column(
            Layout(
                renderable=Text.assemble(
                    Text.from_markup(
                        f"[bold]Summary:[/bold] {info.info.summary if info.info.summary else 'N/A'}\n"
                    ),
                    Text.from_markup(
                        f"[bold]License:[/bold] {info.info.license if info.info.license else 'N/A'}\n"
                    ),
                    Text.from_markup(
                        f"[bold]Python Version:[/bold] {info.info.requires_python if info.info.requires_python else 'N/A'}\n"
                    ),
                ),
                name="summary",
                size=4,
            ),
            Layout(
                name="attribution",
                size=(
                    (
                        len(info.info.author_email.split(", "))
                        if info.info.author_email
                        else 0
                    )
                    if (
                        len(info.info.author_email.split(", "))
                        if info.info.author_email
                        else 0
                    )
                    > (
                        len(info.info.maintainer_email.split(", "))
                        if info.info.maintainer_email
                        else 0
                    )
                    else (
                        len(info.info.maintainer_email.split(", "))
                        if info.info.maintainer_email
                        else 0
                    )
                )
                + 2,
            ),
            Layout(name="urls", size=len(info.info.project_urls) + 2),
            Layout(name="classifiers", size=class_height),
        )

        # summary height
        dynamic_height += 4

        header_content["attribution"].split_row(
            Text.from_markup(
                f"[bold]Authors:[/bold]\n    {'\n    '.join(info.info.author_email.split(', '))}\n"
                if info.info.author_email
                else "[bold]Authors:[/] N/A"
            ),
            Text.from_markup(
                f"[bold]Maintainers:[/bold]\n    {'\n    '.join(info.info.maintainer_email.split(', '))}"
                if info.info.maintainer_email
                else "[bold]Maintainers:[/] N/A"
            ),
        )

        # attr height
        dynamic_height += (
            (len(info.info.author_email.split(", ")) if info.info.author_email else 0)
            if (
                len(info.info.author_email.split(", ")) if info.info.author_email else 0
            )
            > (
                len(info.info.maintainer_email.split(", "))
                if info.info.maintainer_email
                else 0
            )
            else (
                len(info.info.maintainer_email.split(", "))
                if info.info.maintainer_email
                else 0
            )
        ) + 2

        header_content["urls"].update(
            Text.from_markup(
                f"[bold]URLs:[/bold]\n    {'\n    '.join([('[italic]' + i.split(':', maxsplit=1)[0] + ':[/italic] ' + i.split(':', maxsplit=1)[1]) if ':' in i else i for i in info.info.project_urls])}"
            ),
        )

        # url height
        dynamic_height += len(info.info.project_urls) + 2

        # classifier height
        dynamic_height += class_height
        header_content["classifiers"].update(
            rich.console.Group(
                Text.from_markup("[bold]Classifiers:[/bold]"),
                rich.columns.Columns(
                    renderables=info.info.classifiers,
                    padding=(0, 2),
                    equal=True,
                    expand=True,
                    width=max([len(i) for i in info.info.classifiers]) + 2,
                ),
            )
        )

        header = rich.padding.Padding(
            rich.panel.Panel(
                header_content,
                title=f"{info.info.name} - v{info.info.version}",
                title_align="left",
                height=dynamic_height + 2,
            ),
            1,
        )
        obj.console.print(header)
        obj.console.print(
            rich.panel.Panel(
                (
                    Markdown(info.info.description)
                    if info.info.description
                    else "[italic]No description...[/italic]"
                ),
                title="Description",
            )
        )
