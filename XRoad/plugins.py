import datetime
import logging
from email.utils import parsedate_to_datetime

from zeep.plugins import HistoryPlugin

_logger = logging.getLogger(__name__)


class UXPHistoryPlugin(HistoryPlugin):
    """
    Represents a plugin for handling history-related functionality specific to UXP.

    This class is a specialized extension of the generic HistoryPlugin, designed to
    handle UXP-specific headers, such as transaction ID and transaction date. The
    primary purpose of this plugin is to extract and provide easy access to these
    pieces of information from HTTP headers.

    :ivar last_received: Stores the last received HTTP headers and potentially other
        related data.
    :type last_received: dict
    """
    @property
    def transaction_id(self) -> str:
        """
        Retrieves the transaction ID from the HTTP headers of the last received
        request. This ID is used to track a specific transaction across
        the system.

        :rtype: String
        :return: The transaction ID as a string. If the "uxp-transaction-id" header
            is not present, an empty string is returned.
        """
        transaction: str = self.last_received["http_headers"].get(  # type: ignore
            "uxp-transaction-id", ""
        )
        return transaction

    @property
    def transaction_date(self) -> datetime.datetime | None:
        """
        Retrieves the transaction date from the "Date" field in the HTTP headers. If the "Date"
        field is not a valid datetime format, the current datetime will be returned instead.

        :return: The transaction date parsed as a `datetime.datetime` object or the current
                 datetime if parsing fails.
        :rtype: datetime.datetime | None
        """
        try:
            date = parsedate_to_datetime(
                self.last_received["http_headers"].get("Date", "")  # type: ignore
            )
        except ValueError:
            date = datetime.datetime.now()
        return date
