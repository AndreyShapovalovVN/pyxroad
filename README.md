# X-Road (Trembita) Python Client

- **Version:** 1.5.6
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

## Installation from GitHub

Using pip:

```bash
pip install git+https://github.com/AndreyShapovalovVN/pyxroad.git#egg=pyxroad
```

Or clone and install locally:

```bash
git clone https://github.com/AndreyShapovalovVN/pyxroad.git
cd pyxroad
pip install -e .
```

## Requirements

- lxml >= 5.2.1
- Requests >= 2.32.3
- setuptools >= 68.1.2
- zeep >= 4.0.0
- redis (optional, for Redis cache support)

## Code Quality Checks

Run the same checks locally as in CI:

```bash
ruff check . --extend-exclude 'tests/~*.py'
mypy . --ignore-missing-imports --pretty --show-error-codes --exclude 'tests/~.*\.py$'
pytest --maxfail=2 --disable-warnings --ignore-glob='tests/~*.py'
```

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

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues, questions, and contributions, please visit:
https://github.com/AndreyShapovalovVN/pyxroad
