import logging
import uuid

import requests
from zeep import Plugin, Client
from zeep.exceptions import Fault
from zeep.helpers import serialize_object

_logger = logging.getLogger('XRoad')


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

    def __init__(self, ssu,
                 client=None, service=None,
                 userId='0000000000',
                 protocolVersion='4.0',
                 id='0',
                 *args, **kwargs):
        self.security_server_url = ssu

        addr_fields = (
            'xRoadInstance',
            'memberClass',
            'memberCode',
            'subsystemCode',
            'serviceCode',
            'serviceVersion')

        client = {addr_fields[i]: val for i, val in
                  enumerate(client.split('/'))}

        service = {addr_fields[i]: val for i, val in
                   enumerate(service.split('/'))}

        wsdl = requests.Request(
            'GET', ssu + '/wsdl', params=service).prepare().url

        service['objectType'] = 'SERVICE'
        client['objectType'] = 'SUBSYSTEM'

        plugins = kwargs.get('plugins') or []
        plugins.append(XRoadPlugin(self))
        kwargs['plugins'] = plugins

        super().__init__(wsdl, *args, **kwargs)

        self.set_ns_prefix('xro', "http://x-road.eu/xsd/xroad.xsd")
        self.set_ns_prefix('iden', "http://x-road.eu/xsd/identifiers")

        self.set_default_soapheaders(
            {
                'client': client,
                'service': service,
                'userId': userId,
                'id': id,
                'protocolVersion': protocolVersion
            }
        )

    def request(self, **kwargs):
        try:
            service = self._default_soapheaders.get('service').get(
                'serviceCode')
        except Exception as err:
            _logger.error(err)
            return None
        else:
            if kwargs.get('xroad_id'):
                self.id = kwargs.get('xroad_id')
                del kwargs['xroad_id']
            try:
                responce = self.service[service](**kwargs)
            except Fault as error:
                _logger.error('service error %s: %s', error.code, error.message)
                raise
            else:
                return serialize_object(responce)

    @property
    def id(self):
        return self._default_soapheaders.get('id')

    @id.setter
    def id(self, value):
        h = self._default_soapheaders
        h['id'] = value
        self.set_default_soapheaders(h)

    @property
    def userId(self):
        return self._default_soapheaders.get('userId')

    @userId.setter
    def userId(self, value):
        h = self._default_soapheaders
        h['userId'] = value
        self.set_default_soapheaders(h)
