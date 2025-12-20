import logging

_logger = logging.getLogger(__name__)

import hashlib
from zeep.cache import Base
from redis import Redis


class RedisCache(Base):
    """
        Redis-based cache for Zeep WSDL/XSD loading.

        - Uses Redis TTL for expiration
        - Stores data as bytes only
        - Hashes URL to keep Redis keys short and safe
        """
    _version = "1"

    def __init__(self, path=None, timeout=3600):
        if isinstance(path, str):
            self.redis_client = Redis.from_url(path)
        elif isinstance(path, Redis):
            self.redis_client = path
        else:
            raise TypeError("path must be str or Redis")
        self.ttl = timeout
        self.prefix = "zeep:cache:"

    def _key(self, url: str) -> str:
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return f"{self.prefix}{digest}"

    def add(self, url, content):
        _logger.debug("Caching contents of %s", url)
        key = self._key(url)
        self.redis_client.set(key, content, ex=self.ttl)

    def get(self, url):
        key = self._key(url)
        content = self.redis_client.get(key)
        if content:
            _logger.debug("Cache HIT for %s", url)
            return content
        _logger.debug("Cache MISS for %s", url)
        return None
