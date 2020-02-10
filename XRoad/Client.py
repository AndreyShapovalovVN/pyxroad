import requests
from zeep import Plugin, Client, xsd
import uuid
import logging

_logger = logging.getLogger('XRoad')

header = xsd.ComplexType(
    [xsd.Element(
        '{http://x-road.eu/xsd/xroad.xsd}client',
        xsd.ComplexType(
            [xsd.Attribute('{http://x-road.eu/xsd/identifiers}'
                           'objectType', xsd.String()),
             xsd.Element('{http://x-road.eu/xsd/identifiers}'
                         'xRoadInstance', xsd.String()),
             xsd.Element('{http://x-road.eu/xsd/identifiers}'
                         'memberClass', xsd.String()),
             xsd.Element('{http://x-road.eu/xsd/identifiers}'
                         'memberCode', xsd.String()),
             xsd.Element('{http://x-road.eu/xsd/identifiers}'
                         'subsystemCode', xsd.String()),
             ])),
        xsd.Element(
            '{http://x-road.eu/xsd/xroad.xsd}service',
            xsd.ComplexType(
                [xsd.Attribute('{http://x-road.eu/xsd/identifiers}'
                               'objectType', xsd.String()),
                 xsd.Element('{http://x-road.eu/xsd/identifiers}'
                             'xRoadInstance', xsd.String()),
                 xsd.Element('{http://x-road.eu/xsd/identifiers}'
                             'memberClass', xsd.String()),
                 xsd.Element('{http://x-road.eu/xsd/identifiers}'
                             'memberCode', xsd.String()),
                 xsd.Element('{http://x-road.eu/xsd/identifiers}'
                             'subsystemCode', xsd.String()),
                 xsd.Element('{http://x-road.eu/xsd/identifiers}'
                             'serviceCode', xsd.String()),
                 ]), ),
        xsd.Element('{http://x-road.eu/xsd/xroad.xsd}'
                    'userId', xsd.String()),
        xsd.Element('{http://x-road.eu/xsd/xroad.xsd}'
                    'id', xsd.String()),
        xsd.Element('{http://x-road.eu/xsd/xroad.xsd}'
                    'protocolVersion', xsd.String()),
    ],
)


class XRoadPlugin(Plugin):
    def __init__(self, xroad_client):
        self.xroad_client = xroad_client

    def ingress(self, envelope, http_headers, operation):
        header = envelope.find(
            '{http://schemas.xmlsoap.org/soap/envelope/}Header')
        if header is None:
            return envelope, http_headers

        for el_name in ['requestHash', 'protocolVersion', 'issue']:
            el = header.find('xro:%s' % el_name)
            if el is not None:
                header.remove(el)
        return envelope, http_headers

    def egress(self, envelope, http_headers, operation, binding_options):
        # Set serviceCode based on the SOAP request
        header = envelope.find(
            '{http://schemas.xmlsoap.org/soap/envelope/}Header')
        if header is None:
            return envelope, http_headers

        el = header.find('xro:id')
        if not el.text:
            el.text = uuid.uuid4().hex

        el = header.find('xro:protocolVersion')
        el.text = '4.0'

        for el in header.getchildren():
            if el.prefix == 'wsa':
                header.remove(el)

        binding_options['address'] = self.xroad_client.security_server_url
        return envelope, http_headers


class XClient(Client):

    def __init__(self, wsdl,
                 client=None, service=None,
                 protocolVersion=4.0,
                 userId='?',
                 id='?',
                 *args, **kwargs):
        self.security_server_url = wsdl

        client = client.split('/')
        service = service.split('/')
        service.append(None)
        assert len(client) == 4
        assert len(service) in (5, 6)
        client = {
            'objectType': 'SUBSYSTEM',
            'xRoadInstance': client[0],
            'memberClass': client[1],
            'memberCode': client[2],
            'subsystemCode': client[3]
        }
        service = {
            'objectType': 'SERVICE',
            'xRoadInstance': service[0],
            'memberClass': service[1],
            'memberCode': service[2],
            'subsystemCode': service[3],
            'serviceCode': service[4]
        }

        if '/wsdl' not in wsdl:
            wsdl = requests.Request(
                'GET', wsdl + '/wsdl', params=service
            ).prepare().url

        plugins = kwargs.get('plugins') or []
        plugins.append(XRoadPlugin(self))
        kwargs['plugins'] = plugins

        super().__init__(wsdl, *args, **kwargs)

        self.set_ns_prefix('xro', "http://x-road.eu/xsd/xroad.xsd")
        self.set_ns_prefix('iden', "http://x-road.eu/xsd/identifiers")

        self.set_default_soapheaders(
            header(client=client, service=service, userId=userId, id=id, )
        )
