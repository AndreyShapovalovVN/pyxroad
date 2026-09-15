# X-Road (Trembita) Python Client

- **Version:** 1.5.10
- **Web:** https://trembita.gov.ua
- **Repository:** https://github.com/AndreyShapovalovVN/pyxroad
- **Keywords:** x-road, xroad, trembita, python, soap

A powerful Python client library for interacting with X-Road (Trembita) security servers.
This library provides a convenient wrapper around the SOAP-based X-Road protocol, allowing
developers to easily integrate X-Road services into their Python applications.

## Supported Python Versions

- Python 3.10+
- Python 3.11+
- Python 3.12+

## Features

- Easy-to-use SOAP client for X-Road services
- Support for multiple cache backends (SQLite, Redis, In-Memory)
- Automatic SOAP header management
- Transaction ID tracking
- Configurable logging
- Type hints for better IDE support

## Installation and development with uv

Install [uv](https://docs.astral.sh/uv/getting-started/installation/).
To add pyxroad to another uv project:

```bash
uv add git+https://github.com/AndreyShapovalovVN/pyxroad.git
```

To work on this repository:

```bash
git clone https://github.com/AndreyShapovalovVN/pyxroad.git
cd pyxroad
uv sync --locked --extra dev
```

uv creates `.venv` and installs the project and development tools. The
`.python-version` file selects Python 3.12 for development and CI; the library
continues to support Python 3.10+. For runtime dependencies only, use
`uv sync --locked`.

Dependencies are declared in `pyproject.toml`; `uv.lock` records exact versions.
Commit both files when changing dependencies with `uv add`, `uv remove`, or
`uv lock --upgrade-package PACKAGE`. Refresh the component license inventory
when runtime dependencies change. `--locked` rejects a stale lockfile.

## Code Quality Checks

Run the same checks locally as in CI:

```bash
uv run --locked --extra dev python scripts/check_licenses.py
uv run --locked --extra dev ruff check . --extend-exclude 'tests/~*.py'
uv run --locked --extra dev mypy . --ignore-missing-imports --pretty --show-error-codes
uv run --locked --extra dev pytest --maxfail=2 --disable-warnings --ignore-glob='tests/~*.py'
```

## Build and publish

Build using the setuptools version installed from `uv.lock`, then verify that
both distributions contain the license materials:

```bash
uv sync --locked
uv build --no-build-isolation
uv run --locked python scripts/check_licenses.py --dist-dir dist
```

The release workflow runs tests and these checks, then publishes with
`uv publish --trusted-publishing always` using the existing PyPI Trusted Publisher
and `pypi` GitHub environment.

## Quick Start

Basic usage example:

```python
from XRoad import XClient, Transport, SqliteCache
import logging
import sys

# Configure logging
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
_logger = logging.getLogger('XRoad')

# Create a client instance
client = XClient(
    ssu="http://security-server:8080",
    client='SEVDEIR-TEST/GOV/00013480/100001',
    service='SEVDEIR-TEST/GOV/00032684/MIA_prod/CheckPassportStatus/v0.1'
)

# Make a service request
try:
    response = client.request(
        xroad_id='ABCD123456',  # Optional: set custom request ID
        PasNumber='AA123456',
        PasSerial='654321'
    )
    _logger.info(f"Response: {response}")
except Exception as err:
    _logger.error(f"Error: {err}")
```

## Advanced Usage

Using custom caching backend:

```python
from XRoad import XClient, Transport, RedisCache

# With Redis cache
redis_cache = RedisCache(path='redis://localhost:6379/0', timeout=3600)
transport = Transport(cache=redis_cache)

client = XClient(
    ssu="http://security-server:8080",
    client='SEVDEIR-TEST/GOV/00013480/100001',
    service='SEVDEIR-TEST/GOV/00032684/MIA_prod/CheckPassportStatus/v0.1',
    transport=transport
)
```

`RedisCache` now has a safe fallback: if `redis` package is not installed or Redis server is unavailable,
it returns `InMemoryCache(timeout=...)` instead of raising an exception.

Setting custom headers:

```python
client.userId = '0123456789'  # Custom user ID
client.id = 'ABCD123456'      # Custom request ID
```

## Available Cache Types

- **InMemoryCache**: Default, stores cache in application memory
- **SqliteCache**: Persistent cache using SQLite database
- **RedisCache**: Distributed cache using Redis

## License

This project is licensed under the [MIT License](LICENSE). Third-party components
retain their own licenses. See the [component inventory](licenses.md) and
[third-party notices and redistribution guidance](THIRD_PARTY_NOTICES.md).

## Support

For issues, questions, and contributions, please visit:
https://github.com/AndreyShapovalovVN/pyxroad
