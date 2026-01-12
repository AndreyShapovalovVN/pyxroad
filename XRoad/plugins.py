import logging

from zeep.plugins import HistoryPlugin

_logger = logging.getLogger(__name__)


class UXPHistoryPlugin(HistoryPlugin):
    @property
    def transaction_id(self):
        return self.last_received["http_headers"].get("uxp-transaction-id")

    @property
    def transaction_date(self):
        return self.last_received["http_headers"].get("Date")
