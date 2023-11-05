import logging
import uuid

from zeep import Client
from zeep.cache import InMemoryCache
from zeep.exceptions import Fault
from zeep.helpers import serialize_object
from zeep.transports import Transport

from .Uxp import Uxp, ADDR_FIELDS

_logger = logging.getLogger('XRoad')


class XClient(Uxp, Client):
    _version = 4.0

    def __init__(self, ssu, client, service, **kwargs):
        Uxp.__init__(self, ssu, client, service, **kwargs)

        self.response = None
        self.headers = {
            'client': self._client,
            'service': self._service,
            'user_id': self._client.get('subsystemCode'),
            'id': uuid.uuid4().hex,
            'protocolVersion': self._version,
            'Issue': None,
            'purposeID': None
        }
        self.headers['client'].update({'objectType': 'SUBSYSTEM'})
        self.headers['service'].update({'objectType': 'SERVICE'})
        transport = kwargs.get('transport')

        Client.__init__(
            self,
            self.get_wsdl_url,
            transport=transport if transport else Transport(InMemoryCache(timeout=60)),
            **kwargs)

        self.transport.session.proxies.update({'http': ssu, })

        self.set_ns_prefix('xro', 'https://x-road.eu/xsd/xroad.xsd')
        self.set_ns_prefix('iden', 'https://x-road.eu/xsd/identifiers')

        self.set_default_soapheaders(self.headers)

        _logger.debug('Default header (%s)', self._default_soapheaders)

    def request(self, **kwargs) -> dict:
        super().request(**kwargs)
        service = self._default_soapheaders['service'].get('serviceCode')
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
        h = self._default_soapheaders
        h['id'] = value
        self.set_default_soapheaders(h)
        _logger.debug('Set (id: %s)', value)

    @property
    def user_id(self):
        return self._default_soapheaders.get('user_id')

    @user_id.setter
    def user_id(self, value):
        h = self._default_soapheaders
        h['user_id'] = value
        self.set_default_soapheaders(h)
        _logger.debug('Set (user_id: %s)', value)

    @property
    def issue(self):
        return self._default_soapheaders.get('user_id')

    @issue.setter
    def issue(self, value):
        h = self._default_soapheaders
        h['Issue'] = value
        self.set_default_soapheaders(h)
        _logger.debug('Set (Issue: %s)', value)

    @property
    def purposeID(self) -> str:
        return self._default_soapheaders.get('purposeID')


    @purposeID.setter
    def purposeID(self, value: str):
        h = self._default_soapheaders
        h['purposeID'] = value
        self.set_default_soapheaders(h)
        _logger.debug('Set (purposeID: %s)', value)
