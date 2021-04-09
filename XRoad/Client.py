import logging
import uuid
from urllib import parse

from zeep import Plugin, Client
from zeep.exceptions import Fault
from zeep.helpers import serialize_object

_logger = logging.getLogger('XRoad')

ADDR_FIELDS = (
    'xRoadInstance',
    'memberClass',
    'memberCode',
    'subsystemCode',
    'serviceCode',
    'serviceVersion')


class XRoadPlugin(Plugin):
    def __init__(self, xroad_client):
        self.xroad_client = xroad_client

    def ingress(self, envelope, http_headers, operation):
        header = envelope.find(
            '{http://schemas.xmlsoap.org/soap/envelope/}Header')
        if header is None:
            return envelope, http_headers

        for el_name in ['requestHash', 'issue']:
            el = header.find('{http://x-road.eu/xsd/xroad.xsd}%s' % el_name)
            if el is not None:
                header.remove(el)
        return envelope, http_headers

    def egress(self, envelope, http_headers, operation, binding_options):
        # Set serviceCode based on the SOAP request
        header = envelope.find(
            '{http://schemas.xmlsoap.org/soap/envelope/}Header')
        if header is None:
            return envelope, http_headers

        el = header.find('{http://x-road.eu/xsd/xroad.xsd}id')
        if el.text == '0':
            el.text = uuid.uuid4().hex

        el = header.find('{http://x-road.eu/xsd/xroad.xsd}userId')
        if el.text == '0000000000':
            client = header.find('{http://x-road.eu/xsd/xroad.xsd}client')
            ssc = client.find('{http://x-road.eu/xsd/identifiers}subsystemCode')
            el.text = ssc.text

        for el in header.getchildren():
            if el.prefix == 'wsa':
                header.remove(el)

        binding_options['address'] = self.xroad_client.security_server_url
        return envelope, http_headers


class XClient(Client):
    _version = 4.0

    def __init__(self, ssu, client, service, *args, **kwargs):
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
