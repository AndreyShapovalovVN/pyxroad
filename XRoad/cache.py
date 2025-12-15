import logging

_logger = logging.getLogger(__name__)

from zeep.cache import Base
from redis import Redis


class RedisCache(Base):
    _version = "1"

    def __init__(self, path=None, timeout=3600):
        self.redis_client = Redis(connection_pool=path)
        self.ttl = timeout

    def add(self, url, content):
        _logger.debug("Caching contents of %s", url)
        if not isinstance(content, (str, bytes)):
            raise TypeError(
                "a bytes-like object is required, not {}".format(type(content).__name__)
            )
        self.redis_client.set(f"xRoad:cach:{url}", content, ex=self.ttl)

    def get(self, url):
        content = self.redis_client.get(f"xRoad:cach:{url}")
        if content:
            _logger.debug("Cache HIT for %s", url)
            return content
        _logger.debug("Cache MISS for %s", url)
        return None
