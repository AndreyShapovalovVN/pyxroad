import logging
import uuid

from zeep import Client
from zeep.cache import InMemoryCache
from zeep.exceptions import Fault
from zeep.helpers import serialize_object
from zeep.transports import Transport

from .Members import Members

_logger = logging.getLogger("XRoad")


class XClient(Client):
    """
    A specialized client class for interacting with X-Road services.

    This class extends the base Client class and provides a mechanism to interact
    with X-Road systems by implementing SOAP-based service requests. It also manages
    the construction of appropriate SOAP headers and using default namespaces
    required by the X-Road environment. The class is capable of handling session
    setup, ensuring proper initialization of member and service objects, and
    handling request serialization.

    :ivar response: Holds the response of the latest SOAP request.
    :type response: Any
    """

    _version = 4.0

    def __init__(
            self, ssu: str, client: str, service: str, transport: object | None = None, *args, **kwargs
    ):
        """
        Initializes an instance of the class, configuring service and client details along with
        SOAP header and transport setup. Validates the presence of required parameters and sets
        default SOAP headers used for communication.

        :param ssu: The subsystem uniform resource identifier or endpoint to connect.
        :type ssu: String
        :param client: The client subsystem identifier in the X-Road ecosystem.
        :type client: String
        :param service: The service identifier within the X-Road ecosystem to be accessed.
        :type service: String
        :param transport: Optional transport object for handling HTTP requests. Defaults
            to an instance of `Transport` with in-memory caching if not provided.
        :type transport: Object | None
        :param args: Additional positional arguments to be passed to the parent class
            initializer.
        :param kwargs: Additional keyword arguments to be passed to the parent class
            initializer.

        :raises ValueError: If the `service` parameter is not provided.
        :raises ValueError: If the `client` parameter is not provided.
        """

        self.response = None

        if not service:
            raise ValueError("service - required")
        if not client:
            raise ValueError("client - required")

        client = Members(objectType="SUBSYSTEM", memberPath=client)
        service = Members(objectType="SERVICE", memberPath=service)

        super().__init__(
            service.wsdl_url(ssu),
            transport=transport if transport else Transport(InMemoryCache(timeout=60)),
            *args,
            **kwargs,
        )

        self.transport.session.proxies.update({"http": ssu, })

        self.set_ns_prefix("xro", "https://x-road.eu/xsd/xroad.xsd")
        self.set_ns_prefix("iden", "https://x-road.eu/xsd/identifiers")

        self.set_default_soapheaders(
            {
                "client": client.member_dict,
                "service": service.member_dict,
                "userId": client.subsystemCode,
                "id": uuid.uuid4().hex,
                "protocolVersion": self._version,
            }
        )
        _logger.debug("Default header (%s)", self._default_soapheaders)

    def request(self, **kwargs):
        """
        Handles SOAP service requests with the ability to specify custom arguments and
        default configurations. The method attempts to process the request with the
        specified arguments, perform serialization of the response object, and handle
        any potential SOAP Fault exceptions that may occur.

        :param kwargs: Arbitrary keyword arguments to be passed to the SOAP service
            request. These may include service-specific parameters or optional settings.
            If an argument with the key 'xroad_id' is supplied, it will set the 'id'
            attribute of the instance.
        :return: Serialized response object from the SOAP service.
        :rtype: Any
        :raises Fault: If a SOAP Fault exception occurs during the service call, it is
            raised after logging the error details.
        """

        service = self._default_soapheaders["service"].get("serviceCode")
        if "xroad_id" in kwargs:
            self.id = kwargs.pop("xroad_id")

        try:
            response = self.service[service](**kwargs)
        except Fault as error:
            _logger.error("service error (%s: %s)", error.code, error.message)
            raise Fault(error)
        else:
            s_object = serialize_object(response)
            _logger.debug("Response (%s)", s_object)
            return s_object

    @property
    def id(self):
        """
        Provides access to the `id` property representing a specific identifier contained within the
        default SOAP header. This property fetches and returns the associated identifier value from
        a predefined key called "id" in the default SOAP headers.

        The property is read-only and allows retrieval of the value, but no direct modifications
        to the object’s underlying internal data structures.

        :rtype: Any
        :return: The value corresponding to the "id" key in the default SOAP headers.
        """
        return self._default_soapheaders.get("id")

    @id.setter
    def id(self, value):
        """
        Sets the value of the `id` attribute and updates the corresponding SOAP
        headers. This setter ensures that the `id` value is synchronized with
        the default SOAP headers and logs the operation for debugging purposes.

        :param value: The new value to set for the `id` attribute. This value
            is used to update the `_default_soapheaders`.
        :type value: Any
        """

        self._default_soapheaders["id"] = value
        self.set_default_soapheaders(self._default_soapheaders)
        _logger.debug("Set (id: %s)", value)

    @property
    def userId(self) -> str:
        """
        Provides access to the userId obtained from default SOAP headers.

        This property is a getter that retrieves the value of the "userId" field
        from the default SOAP headers set in the object. It is meant to provide a
        convenient way to access this specific information if it exists in the
        SOAP headers.

        :rtype: String
        :return: The value of "userId" from the default SOAP headers if it exists,
            otherwise returns None.
        """
        return self._default_soapheaders.get("userId")

    @userId.setter
    def userId(self, value: str):
        """
        Sets the userId value into the default SOAP headers and updates the headers accordingly.
        Logs the userId value upon setting for debugging purposes.

        :param value: The userId value to be set in the default SOAP headers.
        :type value: String
        """

        self._default_soapheaders["userId"] = value
        self.set_default_soapheaders(self._default_soapheaders)
        _logger.debug("Set (userId: %s)", value)
