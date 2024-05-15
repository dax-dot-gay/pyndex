# pyndex
Self-hosted pypi-compatible package index with deep package access permissioning.

## Table of Contents

- [Features](#features)
- [Planned Features](#planned-features)
- [Installation](#installation)
- [Usage](#usage)
    - [CLI](#cli)
    - [Library](#library)
        - [Client Object](#client-object)
        - [`PackageOperator`](#packageoperator)
        - [`PackageItem`](#packageitem)
        - [`UserOperator`](#useroperator)
        - [`UserItem`](#useritem)
        - [`GroupOperator`](#groupoperator)
        - [`GroupItem`](#groupitem)
    - [Server](#server)

## Features

- Compatibility with the PYPA JSON API & upload API
- Proxying of external package indices (ie PyPi passthrough)
- User- and group-based permissioning
- Local database for increased portability & reduced footprint
- Multiple interface methods (CLI, Python library, direct REST API access)

## Planned Features

- Token-based authentication to allow authentication without providing CI tools with user credentials.

## Installation

--WIP--

## Usage

### CLI

The CLI functions can be accessed through `python -m pyndex ...`. The CLI follows a general `pyndex <command> <subcommand>` format, and each level's help documentation can be accessed with `--help`. The CLI stores local configuration data (connected indices, login info, etc) in the user's config directory by default, although other config files can be passed in as well.

### Library

```python
from pyndex import Pyndex

with Pyndex(host="http://...", api_base="/", username="admin", password="admin").session() as index:
    ...
```

#### Client Object:

The `Pyndex` object is initialized with a host URL, optional API base path, and an optional username & password. It can then either be used as a context manager (`Pyndex().sessoion()`) or activated & deactivated with `Pyndex().connect()` & `Pyndex().disconnect()`.

The activated object has 3 members/operators:

- `Pyndex().package -> PackageOperator`
- `Pyndex().users -> UserOperator`
- `Pyndex().groups -> GroupOperator`

In following sections, an activated `Pyndex` object is represented by `index`.

#### `PackageOperator`:

**Call Signature:**

`index.package(name: str, version: str | None = None, local: bool = False) -> PackageItem | None`:

Retrieves a package based on a name & optional version.
- `name`: Package name (string)
- `version`: Optional string version (None for latest)
- `local`: Whether to only query packages on the local index (ie no proxying)

Returns a `PackageItem` if a result is found, otherwise returns `None`.

**Methods:**

- `index.package.upload(*dists: str, on_progress: (update: ProgressUpdate) -> None | None = None) -> list[PackageItem]`
    
    Uploads package(s) from `dists`, optionally with a provided callback function providing upload progress for each file. Paths passed to `dists` should be glob paths, allowing matching files within the dist folder.

    - `*dists`: Any number of string paths referencing distribution files to upload. For example, `dist/*` will upload all files within the `dist` folder.
    - `on_progress`: A callback that takes one argument containing information about file upload progress. If not provided, no progress callbacks will be called.

    Returns a list of all `PackageItem`s uploaded.

- `index.package.all() -> Iterator[PackageItem]`

    Returns an iterator over all packages hosted on the local index. To alleviate performance concerns, this iterator will load results lazily instead of preemptively.

#### `PackageItem`:

`PackageItem` objects contain metadata about a specific package version, as well as several package-related methods.

**Methods:**

- `package.get_version(version: str) -> PackageItem | None`

    Returns a specific version of the current package, if available. If the current package is locally-hosted, this will only return package versions on the local index.

- `package.get_files() -> list[PackageFileDetail]`:

    Returns a list of all files associated with this package version.

#### `UserOperator`:

**Call Signature:**

`index.users(username: str | None = None, user_id: str | None = None) -> UserItem | None`

Retrieves a specific user, if available. `username` and `user_id` are exclusive arguments, with exactly one being required to query users.

- `username`: Username to search for
- `user_id`: User ID to search for

Returns a `UserItem` if found, otherwise returns `None`.

**Properties:**

- `index.users.active -> UserItem`

    Returns the currently logged-in user. If no user is authenticated, this will raise an `ApiError`.

**Methods:**

- `index.users.all() -> list[UserItem]`

    Returns a list of `UserItem` objects representing all users on the index.

- `index.users.create(username: str, password: str | None = None) -> UserItem`

    Creates a new user, requiring that the authenticated user has administrator permissions.

    - `username`: The desired username for the new user
    - `password`: Optional user password

Returns the created `UserItem` if successful, raising an `ApiError` otherwise.

#### `UserItem`:

`UserItem` contains properties of users, as well as user management methods.

**Methods:**

- `user.delete() -> None`

    Deletes the referenced user. If the user isn't the currently logged-in user, this requires administrator permissions.

- `user.add_permission(spec: PermissionSpecModel) -> list[PermissionSpecModel]`

    Adds a permission to the referenced user. This requires admin permissions for server permissions, and package management permissions for package permissions.

    - `spec`: A BaseModel containing information about which permission to add.

    Returns a list of all permissions held by the user.

    Two additional utility methods are as follows:

    - `add_server_permission(permission: MetaPermission) -> list[PermissionSpecModel]`

        Adds a server permission based on `permission`.
    
    - `add_package_permission(permission: PackagePermission, package: str) -> list[PermissionSpecModel]`

        Adds a package permission to `package`.

- `user.get_permissions(project: str | None = None) -> list[PermissionSpecModel]`

    Gets a list of all permissions held by a user. If `project` is provided, this will only return permissions for the specific project.

    - `project`: Optional package name to query.

- `user.delete_permission(spec: PermissionSpecModel) -> list[PermissionSpecModel]`

    Deletes a permission from the user.

    - `spec`: A BaseModel specifying a permission to remove.

    Returns a list of all permissions held by the user

    Two additional utility methods are as follows:

    - `delete_server_permission(permission: MetaPermission) -> list[PermissionSpecModel]`

        Removes a server permission based on `permission`.
    
    - `delete_package_permission(permission: PackagePermission, package: str) -> list[PermissionSpecModel]`

        Removes a package permission from `package`.

- `user.change_password(current_password: str | None, new_password: str | None) -> None`

    Changes the password of the current user. If attempted on a non-current user, will raise `RuntimeError`.

    - `current_password`: The current user password, or `None` if no password is set.
    - `new_password`: The new password, or `None` to remove the password.

#### `GroupOperator`:

**Call Signature:**

`index.groups(group_id: str | None = None, group_name: str | None = None) -> GroupItem | None`

Finds a group by ID or name (exclusive).

- `group_id`: Group ID to find (cannot be provided with `group_name`)
- `group_name`: Group name to find (cannot be provided with `group_id`)

Returns a `GroupItem` if found, otherwise returns `None`.

**Methods:**

- `index.groups.create(name: str, display_name: str | None = None) -> GroupItem`

    Creates a new group, requiring administrator permissions.

    - `name`: Unique group name
    - `display_name`: Optional human-friendly display name

    Returns `GroupItem` created.

- `index.groups.all() -> list[GroupItem]`

    Returns a list of all groups on the local index.

#### `GroupItem`:

Contains properties & management methods for the referenced group.

**Methods:**

- `group.add_member(member: UserItem) -> None`

    Adds `member` to the group, requiring admin permissions

    - `member`: `UserItem` to add to the group.

- `group.delete_member(member: UserItem) -> None`

    Removes `member` from the group, requiring admin permissions

    - `member`: `UserItem` to remove from the group.

- `group.get_members() -> list[UserItem]`

    Returns a list of all `UserItem` members of the group.

- `group.delete() -> None`

    Deletes the group, requiring admin permissions

- `group.add_permission(spec: PermissionSpecModel) -> list[PermissionSpecModel]`

    Adds a permission to the referenced group. This requires admin permissions for server permissions, and package management permissions for package permissions.

    - `spec`: A BaseModel containing information about which permission to add.

    Returns a list of all permissions held by the group.

    Two additional utility methods are as follows:

    - `add_server_permission(permission: MetaPermission) -> list[PermissionSpecModel]`

        Adds a server permission based on `permission`.
    
    - `add_package_permission(permission: PackagePermission, package: str) -> list[PermissionSpecModel]`

        Adds a package permission to `package`.

- `group.get_permissions(project: str | None = None) -> list[PermissionSpecModel]`

    Gets a list of all permissions held by a group. If `project` is provided, this will only return permissions for the specific project.

    - `project`: Optional package name to query.

- `group.delete_permission(spec: PermissionSpecModel) -> list[PermissionSpecModel]`

    Deletes a permission from the group.

    - `spec`: A BaseModel specifying a permission to remove.

    Returns a list of all permissions held by the group

    Two additional utility methods are as follows:

    - `delete_server_permission(permission: MetaPermission) -> list[PermissionSpecModel]`

        Removes a server permission based on `permission`.
    
    - `delete_package_permission(permission: PackagePermission, package: str) -> list[PermissionSpecModel]`

        Removes a package permission from `package`.



### Server

Before deployment, the server requires a config file following the format outlined in [config.test.toml](config.test.toml), in a file named `config.toml` placed in the server's working directory. The server can then be run with `hypercorn pyndex:server`. Production deployment is WIP.
