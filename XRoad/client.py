import logging
import uuid
from urllib import parse

import httpx
from zeep import Client
from zeep.cache import InMemoryCache
from zeep.exceptions import Fault
from zeep.helpers import serialize_object
from zeep.transports import Transport

_logger = logging.getLogger('XRoad')

ADDR_FIELDS = (
    'xRoadInstance',
    'memberClass',
    'memberCode',
    'subsystemCode',
    'serviceCode',
    'serviceVersion')


class XRoadClient:
    def __init__(self, protokol, *args, **kwargs):
        if protokol == 'SOAP':
            self.client = XClient(*args, **kwargs)
        elif protokol == 'REST':
            self.client = RClient(*args, **kwargs)
        else:
            raise ValueError('Supported protocols only SOAP and REST')


class RClient:
    _version = 'r1'

    def __init__(self, ssu, client, service, **kwargs):
        if not service:
            raise Exception('service - required')
        if not client:
            raise Exception('client - required')

        self.headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json',
            'X-Road-Client': client,
            'X-Road-Service': service,
            'X-Road-Id': uuid.uuid4().hex,
            'X-Road-UserId': {ADDR_FIELDS[i]: val for i, val in enumerate(client.split('/'))}.get('subsystemCode'),
            'X-Road-Issue': None
        }
        self.uri = '/'.join((self._version, service, kwargs.get('uri')))
        self.url = '/'.join((ssu, self.uri))

        self.http_type = kwargs.get('type') or 'GET'

    def request(self, **kwargs):
        if kwargs.get('xroad_id'):
            self.id = kwargs.get('xroad_id')
            del kwargs['xroad_id']

        if kwargs.get('xroad_issue'):
            self.issue(kwargs.get('xroad_issue'))
            del kwargs['xroad_issue']

        _logger.debug('URL: %s', self.url)
        _logger.debug('Type: %s', self.http_type)
        _logger.debug('Headers: %s', self.headers)
        _logger.debug('Data: %s', kwargs)

        response = httpx.request(self.http_type, self.url, headers=self.headers, data=kwargs, timeout=60)

        _logger.debug('Response status code: %s', response.status_code)
        _logger.debug(response.content)

        if response.status_code == 200:
            return response.json()

    @property
    def id(self):
        return self.headers.get('X-Road-Id')

    @id.setter
    def id(self, value):
        self.headers.update({'X-Road-Id': value})
        _logger.debug('Set (id: %s)', value)

    @property
    def user_id(self):
        return self.headers.get('X-Road-UserId')

    @user_id.setter
    def user_id(self, value):
        self.headers.update({'X-Road-UserId': value})
        _logger.debug('Set (user_id: %s)', value)

    @property
    def issue(self):
        return self.headers.get('X-Road-Issue')

    @issue.setter
    def issue(self, value):
        self.headers.update({'X-Road-Issue': value})
        _logger.debug('Set (Issue: %s)', value)


class XClient(Client):
    _version = 4.0

    def __init__(self, ssu, client, service, *args, **kwargs):
        if not service:
            raise Exception('service - required')
        if not client:
            raise Exception('client - required')

        self._ssu = ssu
        self._service = {ADDR_FIELDS[i]: val for i, val in enumerate(service.split('/'))}
        self._client = {ADDR_FIELDS[i]: val for i, val in enumerate(client.split('/'))}

        self.response = None
        self.headers = {
            'client': self._client,
            'service': self._service,
            'user_id': self._client.get('subsystemCode'),
            'id': uuid.uuid4().hex,
            'protocolVersion': self._version,
            'Issue': None
        }
        self.headers['client'].update({'objectType': 'SUBSYSTEM'})
        self.headers['service'].update({'objectType': 'SERVICE'})
        transport = kwargs.get('transport')

        super().__init__(
            self.get_wsdl_url,
            transport=transport if transport else Transport(InMemoryCache(timeout=60)),
            *args, **kwargs)

        self.transport.session.proxies.update({'http': ssu, })

        self.set_ns_prefix('xro', 'https://x-road.eu/xsd/xroad.xsd')
        self.set_ns_prefix('iden', 'https://x-road.eu/xsd/identifiers')

        self.set_default_soapheaders(self.headers)

        _logger.debug('Default header (%s)', self._default_soapheaders)

    def request(self, **kwargs):
        service = self._default_soapheaders['service'].get('serviceCode')

        if kwargs.get('xroad_id'):
            self.id = kwargs.get('xroad_id')
            del kwargs['xroad_id']

        if kwargs.get('xroad_issue'):
            self.issue(kwargs.get('xroad_issue'))
            del kwargs['xroad_issue']

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
    def get_wsdl_url(self):
        s = self._service.copy()
        if s.get('objectType'):
            del s['objectType']
        if s.get('serviceVersion'):
            s.update({'version': s.get('serviceVersion')})
            del s['serviceVersion']
        u = parse.urlparse(self._ssu)
        _logger.debug(s)
        return parse.urlunparse(u._replace(path='wsdl', query=parse.urlencode(s)))
