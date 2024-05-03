import logging
import os
from typing import Any, Callable, Literal, cast
from pydantic import BaseModel
from twine.commands.upload import skip_upload, _make_package
from requests.models import Response as Response
from twine.package import PackageFile
from twine.repository import Repository
from twine.settings import Settings
from twine.utils import DEFAULT_CONFIG_FILE
from twine import commands, exceptions, utils
import requests_toolbelt

logger = logging.getLogger("pyndex")


class ProgressUpdate_Upload(BaseModel):
    action: Literal["upload"] = "upload"
    filename: str
    completed: int
    total: int


class ProgressUpdate_Start(BaseModel):
    action: Literal["start"] = "start"
    filename: str


ProgressUpdate = ProgressUpdate_Start | ProgressUpdate_Upload


class WrappedRepo(Repository):
    def __init__(
        self,
        repository_url: str,
        username: str | None,
        password: str | None,
        settings: "WrappedSettings",
    ) -> None:
        """Wrapper around Repository that provides callback functions & removes print output

        Args:
            repository_url (str): Repo URL
            username (str | None): Username, if required
            password (str | None): Password, if required
            settings (WrappedSettings): WrappedSettings object w/ callback
        """
        super().__init__(repository_url, username, password, True)
        self.settings = settings

    def _upload(self, package: PackageFile) -> Response:
        """Patched Repository._upload to replace rich output w/ callbacks

        Args:
            package (PackageFile): Package to upload

        Returns:
            Response: Response info
        """
        self.settings.on_progress(ProgressUpdate_Start(filename=package.basefilename))
        data = package.metadata_dictionary()
        data.update(
            {
                # action
                ":action": "file_upload",
                "protocol_version": "1",
            }
        )

        data_to_send = self._convert_data_to_list_of_tuples(data)

        with open(package.filename, "rb") as fp:
            data_to_send.append(
                ("content", (package.basefilename, fp, "application/octet-stream"))
            )
            encoder = requests_toolbelt.MultipartEncoder(data_to_send)
            total = encoder.len
            monitor = requests_toolbelt.MultipartEncoderMonitor(
                encoder,
                lambda monitor: self.settings.on_progress(
                    ProgressUpdate_Upload(
                        filename=package.basefilename,
                        completed=monitor.bytes_read,
                        total=total,
                    )
                ),
            )

            resp = self.session.post(
                self.url,
                data=monitor,
                allow_redirects=False,
                headers={"Content-Type": monitor.content_type},
            )

        return resp


class WrappedSettings(Settings):

    def __init__(
        self,
        *,
        sign: bool = False,
        sign_with: str = "gpg",
        identity: str | None = None,
        username: str | None = None,
        password: str | None = None,
        non_interactive: bool = False,
        comment: str | None = None,
        config_file: str = DEFAULT_CONFIG_FILE,
        skip_existing: bool = False,
        cacert: str | None = None,
        client_cert: str | None = None,
        repository_name: str = "pypi",
        repository_url: str | None = None,
        verbose: bool = False,
        disable_progress_bar: bool = False,
        progress_callback: Callable[[ProgressUpdate], None] | None = None,
        **ignored_kwargs: Any,
    ) -> None:
        """WrappedSettings initializer

        Args:
            progress_callback (Callable[[ProgressUpdate], None] | None, optional): Callback to call on upload progress. Defaults to None.
            **kwargs (Any, Optional): All other kwargs are passed to Settings.
        """
        super().__init__(
            sign=sign,
            sign_with=sign_with,
            identity=identity,
            username=username,
            password=password,
            non_interactive=non_interactive,
            comment=comment,
            config_file=config_file,
            skip_existing=skip_existing,
            cacert=cacert,
            client_cert=client_cert,
            repository_name=repository_name,
            repository_url=repository_url,
            verbose=verbose,
            disable_progress_bar=disable_progress_bar,
            **ignored_kwargs,
        )
        self.progress_callback = progress_callback

    def on_progress(self, update: ProgressUpdate) -> None:
        """Wrapper function that is a no-op if a callback is not defined.

        Args:
            update (ProgressUpdate): Update passed to callback
        """
        if self.progress_callback:
            self.progress_callback(update)

    def create_repository(self) -> "WrappedRepo":
        """Wraps Settings.create_repository() to add callback passing

        Returns:
            WrappedRepo: A WrappedRepo instance
        """
        repo = WrappedRepo(
            cast(str, self.repository_config["repository"]),
            self.username,
            self.password,
            self,
        )
        repo.set_certificate_authority(self.cacert)
        repo.set_client_certificate(self.client_cert)
        return repo


def upload(
    *dists: str,
    progress_callback: Callable[[ProgressUpdate], None] | None = None,
    repository_name: str | None = None,
    repository_url: str | None = None,
    username: str = "",
    password: str = "",
    **kwargs,
) -> set[tuple[str, str]]:
    """A library-friendly wrapper around twine.commands.upload.upload

    Args:
        *dists (str): Any number of paths/globs to upload (ie "dist/*").
        progress_callback (Callable[[ProgressUpdate], None] | None, optional): A callback to call on upload progress. Takes one positional argument, a ProgressUpdate with update info. Defaults to None.
        repository_name (str | None, optional): Repo name to upload to (as defined in .pypirc). Defaults to None.
        repository_url (str | None, optional): Repo URL to upload to (ie https://upload.pypi.org). Defaults to None.
        username (str, optional): Index username, if required. Defaults to "".
        password (str, optional): Index password, if required. Defaults to "".
        **kwargs (Any, optional): Additional keyword arguments to pass to Settings.

    Returns:
        set[tuple[str, str]]: Set of (package name, package version) uploaded

    Attribution:
        Main code is attributed to https://github.com/pypa/twine/blob/48af4c1bd476334d7360ca854537116afeeffd43/twine/commands/upload.py#L94, licensed under the Apache 2.0 license.
        Code has been modified to remove program output unsuitable for headless operation
    """
    upload_settings = WrappedSettings(
        repository_name=repository_name,
        repository_url=repository_url,
        username=username,
        password=password,
        disable_progress_bar=True,
        progress_callback=progress_callback,
        non_interactive=True,
        **kwargs,
    )

    # === Reimplementation of Twine's upload code to remove in-library printing ===

    dists = commands._find_dists(dists)
    # Determine if the user has passed in pre-signed distributions
    signatures = {os.path.basename(d): d for d in dists if d.endswith(".asc")}
    uploads = [i for i in dists if not i.endswith(".asc")]

    upload_settings.check_repository_url()
    repository_url = cast(str, upload_settings.repository_config["repository"])

    packages_to_upload = [
        _make_package(filename, signatures, upload_settings) for filename in uploads
    ]

    if any(p.gpg_signature for p in packages_to_upload):
        if repository_url.startswith((utils.DEFAULT_REPOSITORY, utils.TEST_REPOSITORY)):
            # Warn the user if they're trying to upload a PGP signature to PyPI
            # or TestPyPI, which will (as of May 2023) ignore it.
            # This warning is currently limited to just those indices, since other
            # indices may still support PGP signatures.
            logger.warning(
                "One or more packages has an associated PGP signature; "
                "these will be silently ignored by the index"
            )
        else:
            # On other indices, warn the user that twine is considering
            # removing PGP support outright.
            logger.warning(
                "One or more packages has an associated PGP signature; "
                "a future version of twine may silently ignore these. "
                "See https://github.com/pypa/twine/issues/1009 for more "
                "information"
            )

    repository = upload_settings.create_repository()
    uploaded_packages: list[PackageFile] = []

    if signatures and not packages_to_upload:
        raise exceptions.InvalidDistribution(
            "Cannot upload signed files by themselves, must upload with a "
            "corresponding distribution file."
        )

    for package in packages_to_upload:
        skip_message = (
            f"Skipping {package.basefilename} because it appears to already exist"
        )

        # Note: The skip_existing check *needs* to be first, because otherwise
        #       we're going to generate extra HTTP requests against a hardcoded
        #       URL for no reason.
        if upload_settings.skip_existing and repository.package_is_uploaded(package):
            logger.warning(skip_message)
            continue

        resp = repository.upload(package)
        logger.info(f"Response from {resp.url}:\n{resp.status_code} {resp.reason}")
        if resp.text:
            logger.info(resp.text)

        # Bug 92. If we get a redirect we should abort because something seems
        # funky. The behaviour is not well defined and redirects being issued
        # by PyPI should never happen in reality. This should catch malicious
        # redirects as well.
        if resp.is_redirect:
            raise exceptions.RedirectDetected.from_args(
                repository_url,
                resp.headers["location"],
            )

        if skip_upload(resp, upload_settings.skip_existing, package):
            logger.warning(skip_message)
            continue

        utils.check_status_code(resp, upload_settings.verbose)

        uploaded_packages.append(package)

    uploaded = set([(i.safe_name, i.metadata.version) for i in uploaded_packages])

    # Bug 28. Try to silence a ResourceWarning by clearing the connection
    # pool.
    repository.close()
    return uploaded
