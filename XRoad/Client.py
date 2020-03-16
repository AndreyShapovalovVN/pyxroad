import logging
import uuid

import requests
from zeep import Plugin, Client

_logger = logging.getLogger('XRoad')


class XRoadPlugin(Plugin):
    def __init__(self, xroad_client):
        self.xroad_client = xroad_client

    def ingress(self, envelope, http_headers, operation):
        header = envelope.find(
            '{http://schemas.xmlsoap.org/soap/envelope/}Header')
        if header is None:
            return envelope, http_headers

        for el_name in ['requestHash', 'protocolVersion', 'issue']:
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

        self.xroad_client.id = self.xroad_client.id or uuid.uuid4().hex
        el = header.find('{http://x-road.eu/xsd/xroad.xsd}id')
        if not el.text:
            el.text = self.xroad_client.id

        el = header.find('{http://x-road.eu/xsd/xroad.xsd}userId')
        if not el.text:
            client = header.find('{http://x-road.eu/xsd/xroad.xsd}client')
            el.text = client.find(
                '{http://x-road.eu/xsd/identifiers}subsystemCode'
            ).text

        for el in header.getchildren():
            if el.prefix == 'wsa':
                header.remove(el)

        binding_options['address'] = self.xroad_client.security_server_url
        return envelope, http_headers


class XClient(Client):

    def __init__(self, ssu,
                 client=None, service=None,
                 userId='0000000000',
                 protocolVersion=4.0,
                 id=None,
                 *args, **kwargs):

        self.security_server_url = ssu

        addr_fields = (
            'xRoadInstance',
            'memberClass',
            'memberCode',
            'subsystemCode',
            'serviceCode',
            'serviceVersion')
        service = {addr_fields[i]: val for i, val in
                   enumerate(service.split('/'))}

        wsdl = requests.Request(
            'GET', ssu + '/wsdl', params=service).prepare().url

        service['objectType'] = 'SERVICE'

        client = {addr_fields[i]: val for i, val in
                  enumerate(client.split('/'))}

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

    @property
    def id(self):
        return self._default_soapheaders.get('id')

    @id.setter
    def id(self, value):
        h = self._default_soapheaders
        h['id'] = value
        self.set_default_soapheaders(h)
        self._id = value

    @property
    def userId(self):
        return self._default_soapheaders.get('userId')

    @userId.setter
    def userId(self, value):
        h = self._default_soapheaders
        h['userId'] = value
        self.set_default_soapheaders(h)
