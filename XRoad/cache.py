import hashlib
import logging

from redis import Redis
from zeep.cache import Base

_logger = logging.getLogger(__name__)


class RedisCache(Base):
    """
    Provides a caching mechanism backed by Redis.

    This class is designed for caching purposes, used Redis as the underlying
    storage. It supports caching content with a specified time-to-live (TTL) and
    identifying cached data through unique keys derived from URLs. The cache can
    accommodate both storing and retrieving cached data, making it suitable for
    applications requiring temporary storage of frequently accessed resources.

    :ivar redis_client: A Redis client instance is used to interact with Redis.
    :type redis_client: Redis
    :ivar ttl: The time-to-live (in seconds) for cached content.
    :type ttl: Int
    :ivar prefix: The prefix used to generate cache keys.
    :type prefix: String
    """

    _version = "1"

    def __init__(self, path: str | Redis | None = None, timeout: int = 3600):
        """
        Initializes a cache object for managing data with Redis as a backend.

        :param path: A Redis connection URL as a string or an instance of the Redis client
            object. If none is provided, a TypeError is raised.
        :param timeout: The time-to-live (TTL) for the cached data, specified in seconds.
            Defaults to 3600 seconds (1 hour).

        :raises TypeError: If `path` is not a string or an instance of Redis.
        """
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

    def add(self, url: str, content: bytes):
        """
        Adds content to the cache associated with a specific URL.

        This function caches the provided content using the URL as a key. The content is
        stored in the cache for the configured time-to-live (TTL) period. The key used for
        caching is generated from the URL, which ensures that the content is identifiable
        and retrievable.

        :param url: The URL to serve as the key for caching. It must be a string.
        :param content: The content to cache, provided as a sequence of bytes.
        :return: None
        """
        _logger.debug("Caching contents of %s", url)
        key = self._key(url)
        self.redis_client.set(key, content, ex=self.ttl)

    def get(self, url: str) -> bytes | None:
        """
        Retrieve content from a cache based on the provided URL. If the content is
        found in the cache (cache hit), it is returned. Otherwise, it logs a cache
        miss and returns None.

        :param url: The URL used to retrieve the cached content.
        :type url: String
        :return: The cached content as bytes if the key exists in the cache; None
            otherwise.
        :rtype: Bytes or None
        """
        key = self._key(url)
        content = self.redis_client.get(key)
        if content:
            _logger.debug("Cache HIT for %s", url)
            return content
        _logger.debug("Cache MISS for %s", url)
        return None
