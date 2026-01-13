import datetime
import logging
from email.utils import parsedate_to_datetime

from zeep.plugins import HistoryPlugin

_logger = logging.getLogger(__name__)


class UXPHistoryPlugin(HistoryPlugin):
    @property
    def transaction_id(self) -> str:
        transaction: str = self.last_received["http_headers"].get(  # type: ignore
            "uxp-transaction-id", ""
        )
        return transaction

    @property
    def transaction_date(self) -> datetime.datetime | None:
        try:
            date = parsedate_to_datetime(
                self.last_received["http_headers"].get("Date", "")  # type: ignore
            )
        except ValueError:
            date = datetime.datetime.now()
        return date
