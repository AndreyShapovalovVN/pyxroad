import logging
import uuid
from urllib import parse

from zeep import Client
from zeep.exceptions import Fault
from zeep.helpers import serialize_object
from zeep.cache import SqliteCache, InMemoryCache
from zeep.transports import Transport
from lxml import etree
from zeep.wsdl.utils import etree_to_string

_logger = logging.getLogger('XRoad')

ADDR_FIELDS = (
    'xRoadInstance',
    'memberClass',
    'memberCode',
    'subsystemCode',
    'serviceCode',
    'serviceVersion')


class DRACTransport(Transport):
    def post_xml(self, address, envelope, headers):
        message = etree.tostring(
            envelope, pretty_print=True, xml_declaration=True, encoding="utf-8"
        ).decode('utf-8')

        _logger.debug(f'Source: \n {message}')
        drac_message = ''
        for line in message.splitlines():
            drac_message += line
            if not 'iden:' in line:
                drac_message += '\n'
        _logger.debug(f'Modified: \n {drac_message}')

        return self.post(address, drac_message.encode('utf-8'), headers)


class XClient(Client):
    _version = 4.0

    def __init__(self, ssu, client, service, transport=None, *args, **kwargs):
        self.response = None

        if not service:
            raise Exception('service - required')
        if not client:
            raise Exception('client - required')

        client = {ADDR_FIELDS[i]: val for i, val in
                  enumerate(client.split('/'))}
        client.update({'objectType': 'SUBSYSTEM'})

        service = {ADDR_FIELDS[i]: val for i, val in
                   enumerate(service.split('/'))}
        service.update({'objectType': 'SERVICE'})

        super().__init__(
            _get_wsdl_url(ssu, service),
            transport=transport if transport else Transport(InMemoryCache(timeout=60)),
            *args, **kwargs)

        self.transport.session.proxies.update({'http': ssu, })

        self.set_ns_prefix('xro', "http://x-road.eu/xsd/xroad.xsd")
        self.set_ns_prefix('iden', "http://x-road.eu/xsd/identifiers")

        self.set_default_soapheaders(
            {
                'client': client,
                'service': service,
                'userId': client.get('subsystemCode'),
                'id': uuid.uuid4().hex,
                'protocolVersion': self._version,
            }
        )
        _logger.debug('Default header (%s)', self._default_soapheaders)

    def request(self, **kwargs):
        service = self._default_soapheaders['service'].get('serviceCode')
        if kwargs.get('xroad_id'):
            self.id = kwargs.get('xroad_id')
            del kwargs['xroad_id']
        try:
            response = self.service[service](**kwargs)
        except Fault as error:
            _logger.error('service error (%s: %s)', error.code,
                          error.message)
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
    def userId(self):
        return self._default_soapheaders.get('userId')

    @userId.setter
    def userId(self, value):
        h = self._default_soapheaders
        h['userId'] = value
        self.set_default_soapheaders(h)
        _logger.debug('Set (userId: %s)', value)


def _get_wsdl_url(host, service):
    s = service.copy()
    if s.get('objectType'):
        del s['objectType']
    if s.get('serviceVersion'):
        s.update({'version': s.get('serviceVersion')})
        del s['serviceVersion']
    u = parse.urlparse(host)
    _logger.debug(s)
    return parse.urlunparse(
        u._replace(
            path='wsdl',
            query=parse.urlencode(s))
    )
