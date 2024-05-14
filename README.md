# pyndex
Self-hosted pypi-compatible package index with deep package access permissioning.

## Features

- Compatibility with the PYPA JSON API & upload API
- Proxying of external package indices (ie PyPi passthrough)
- User- and group-based permissioning
- Local database for increased portability & reduced footprint
- Multiple interface methods (CLI, Python library, direct REST API access)

## Installation

--WIP--

## Usage

### CLI

The CLI functions can be accessed through `python -m pyndex ...`. The CLI follows a general `pyndex <command> <subcommand>` format, and each level's help documentation can be accessed with `--help`. The CLI stores local configuration data (connected indices, login info, etc) in the user's config directory by default, although other config files can be passed in as well.

### Library

--WIP--

### Server

Before deployment, the server requires a config file following the format outlined in [config.test.toml](config.test.toml), in a file named `config.toml` placed in the server's working directory. The server can then be run with `hypercorn pyndex:server`. Production deployment is WIP.
