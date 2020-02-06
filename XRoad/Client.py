import requests
import zeep
import uuid
import logging

_logger = logging.getLogger('XRoad')


class XRoadPlugin(zeep.Plugin):
    def __init__(self, xroad_client):
        self.xroad_client = xroad_client

    def ingress(self, envelope, http_headers, operation):
        header = envelope.find(
            '{http://schemas.xmlsoap.org/soap/envelope/}Header')
        if header is None:
            return envelope, http_headers

        remove_elements = ['requestHash', 'protocolVersion', 'issue']
        for el_name in remove_elements:
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
        el.text = uuid.uuid4().hex

        el = header.find('{http://x-road.eu/xsd/xroad.xsd}protocolVersion')
        el.text = '4.0'

        service = header.find('{http://x-road.eu/xsd/xroad.xsd}service')
        el = service.find('{http://x-road.eu/xsd/identifiers}serviceCode')
        if not el.text:
            el.text = operation.name

        # For some reason, zeep insists on adding WSA elements to the
        # header. This will only confuse some servers, so remove the
        # elements here.
        for el in header.getchildren():
            if el.prefix == 'wsa':
                header.remove(el)

        binding_options['address'] = self.xroad_client.security_server_url
        return envelope, http_headers


class Client(zeep.Client):
    HEADER = {}

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

        self.HEADER.update(
            {
                'client': {
                    'xRoadInstance': client[0],
                    'memberClass': client[1],
                    'memberCode': client[2],
                    'subsystemCode': client[3],
                },
                'service': {
                    'xRoadInstance': service[0],
                    'memberClass': service[1],
                    'memberCode': service[2],
                    'subsystemCode': service[3],
                    'serviceCode': service[4],
                    'serviceVersion': service[5],
                },
                'protocolVersion': protocolVersion,
                'userId': userId,
                'id': id,
            }
        )

        if '/wsdl' not in wsdl:
            wsdl = requests.Request(
                'GET',
                wsdl + '/wsdl',
                params=self.HEADER['service']
            ).prepare().url

        plugins = kwargs.get('plugins') or []
        plugins.append(XRoadPlugin(self))
        kwargs['plugins'] = plugins

        super().__init__(wsdl, *args, **kwargs)

        self.set_ns_prefix('xro', "http://x-road.eu/xsd/xroad.xsd")
        self.set_ns_prefix('iden', "http://x-road.eu/xsd/identifiers")

        self.set_default_soapheaders(self.HEADER)
