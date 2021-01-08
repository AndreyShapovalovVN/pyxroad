import datetime
import logging
import sys
import threading

from zeep.cache import _is_expired, VersionedCacheBase

_logger = logging.getLogger('XRoad.Cache')


class PlPuCache(VersionedCacheBase):
    _version = "1"

    def __init__(self, timeout=3600):
        if 'plpy' not in sys.modules:
            raise RuntimeError("Class only Pl/Python")

        self._lock = threading.RLock()
        self._timeout = timeout

        plpy.execute(
            """
                CREATE TABLE IF NOT EXISTS request
                (created timestamp, url text, content text)
            """
        )
        plpy.commit()

    def add(self, url, content):
        _logger.debug("Caching contents of %s", url)
        data = self._encode_data(content)

        plpy.execute("DELETE FROM request WHERE url = ?", (url,))
        plpy.execute(
            "INSERT INTO request (created, url, content) VALUES (?, ?, ?)",
            (datetime.datetime.utcnow(), url, data),
        )
        plpy.commit()

    def get(self, url):
        rows = plpy.execute("SELECT created, content FROM request WHERE url=?",
                            (url,))
        if rows:
            created, data = rows[0]
            if not _is_expired(created, self._timeout):
                _logger.debug("Cache HIT for %s", url)
                return self._decode_data(data)
        _logger.debug("Cache MISS for %s", url)
