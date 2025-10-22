import logging
import uuid

from zeep import Client
from zeep.cache import InMemoryCache
from zeep.exceptions import Fault
from zeep.helpers import serialize_object
from zeep.transports import Transport

from .Members import Members
from .fixBagInWSDL import _hack_wsdl

_logger = logging.getLogger('XRoad')


class XClient(Client):
    """
    XClient is a wrapper around zeep.Client that provides a default header
    for X-Road services. It also provides a method to send requests to the
    service and return the response.
    """
    _version = 4.0

    def __init__(self, ssu, client, service, transport=None, hack_wsdl=False, *args, **kwargs):
        """
        :param ssu: Security Server URL
        :param client:
        :param service:
        :param transport:
        :param hack_wsdl:
        :param args:
        :param kwargs:
        """
        self.response = None

        if not service:
            raise Exception('service - required')
        if not client:
            raise Exception('client - required')

        client = Members(objectType='SUBSYSTEM', memberPath=client)
        service = Members(objectType='SERVICE', memberPath=service)

        wsdl = _hack_wsdl(service.wsdl_url(ssu), service.serviceCode) if hack_wsdl else service.wsdl_url(ssu)

        super().__init__(
            wsdl,
            transport=transport if transport else Transport(InMemoryCache(timeout=60)),
            *args, **kwargs)

        self.transport.session.proxies.update({'http': ssu, })

        self.set_ns_prefix('xro', "http://x-road.eu/xsd/xroad.xsd")
        self.set_ns_prefix('iden', "http://x-road.eu/xsd/identifiers")

        self.set_default_soapheaders({
            'client': client.member_dict,
            'service': service.member_dict,
            'userId': client.subsystemCode,
            'id': uuid.uuid4().hex,
            'protocolVersion': self._version,
        })
        _logger.debug('Default header (%s)', self._default_soapheaders)

    def request(self, **kwargs):
        service = self._default_soapheaders['service'].get('serviceCode')
        if 'xroad_id' in kwargs:
            self.id = kwargs.pop('xroad_id')

        try:
            response = self.service[service](**kwargs)
        except Fault as error:
            _logger.error('service error (%s: %s)', error.code, error.message)
            raise Fault(error)
        else:
            s_object = serialize_object(response)
            _logger.debug('Response (%s)', s_object)
            return s_object

    @property
    def id(self):
        return self._default_soapheaders.get('id')

    @id.setter
    def id(self, value):
        self._default_soapheaders['id'] = value
        self.set_default_soapheaders(self._default_soapheaders)
        _logger.debug('Set (id: %s)', value)

    @property
    def userId(self):
        return self._default_soapheaders.get('userId')

    @userId.setter
    def userId(self, value):
        self._default_soapheaders['userId'] = value
        self.set_default_soapheaders(self._default_soapheaders)
        _logger.debug('Set (userId: %s)', value)
