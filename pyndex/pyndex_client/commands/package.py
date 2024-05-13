from typing import Callable
import click
from ..util import AliasedGroup
from ..models import AppContext
from rich.markdown import Markdown
from rich.progress import Progress
from ...common import ProgressUpdate
from ...pyndex_api.util import ApiError


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
    default=False,
    help="Whether to include full text of markdown description.",
)
@click.option(
    "--files/--no-files",
    "files",
    default=False,
    help="Whether to list associated files.",
)
@click.pass_obj
def show_package(
    obj: AppContext,
    name: str,
    version: str | None,
    local: bool,
    describe: bool,
    files: bool,
):
    """Show detailed information about a specific package by NAME"""

    package = obj.client.package(name, version=version, local=local)
    if package:
        obj.console.print(
            f"[bold]Found [underline]{'Local' if package.local else 'Remote'}[/underline] Package:[/] {package.info.name} v{package.info.version}\n"
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

        if files:
            pkg_files = package.get_files()
            obj.console.print(
                f"\t  [underline]Files[/]          : {'\n' if len(pkg_files) > 0 else '-'}"
            )
            if len(pkg_files) > 0:
                max_name = max([len(i.filename) for i in pkg_files])
                for file in pkg_files:
                    obj.console.print(
                        f"\t    * {file.filename}:{' ' * (max_name - len(file.filename) + 1)}[blue italic]{file.url}[/]"
                    )

    else:
        obj.error("Failed to resolve package.")


@package.command("upload")
@click.option(
    "--dist",
    "-d",
    "dists",
    multiple=True,
    help="Paths to dist folders (ie dist/*) to upload. Can be specified multiple times.",
)
@click.pass_obj
def upload_package(obj: AppContext, dists: tuple[str]):
    """Upload package(s) to the index."""

    def progress_tracker(
        dist: str, progress_bar: Progress, tasks: dict[str, int]
    ) -> Callable[[ProgressUpdate], None]:
        def _track(progress: ProgressUpdate):
            if not progress.filename in tasks.keys():
                tasks[progress.filename] = progress_bar.add_task(
                    f"Uploading {progress.filename} from {dist}..."
                )

            if progress.action == "upload":
                progress_bar.update(
                    tasks[progress.filename],
                    total=progress.total,
                    completed=progress.completed,
                )

        return _track

    for dist in dists:
        obj.console.print(f"Uploading {dist} to {obj.repo.name} ({obj.repo.host})")
        with Progress() as progress:
            tasks = {}
            try:
                obj.client.package.upload(
                    dist, on_progress=progress_tracker(dist, progress, tasks)
                )
            except:
                obj.error(f"Failed to upload {dist}.")
