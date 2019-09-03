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

        service = header.find('{http://x-road.eu/xsd/xroad.xsd}service')
        el = service.find('{http://x-road.eu/xsd/identifiers}serviceCode')
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
    HEADER = {
        'client': {
            'objectType': 'SUBSYSTEM',
            'xRoadInstance': None,
            'memberClass': None,
            'memberCode': None,
            'subsystemCode': None,
        },
        'service': {
            'objectType': "SERVICE",
            'xRoadInstance': None,
            'memberClass': None,
            'memberCode': None,
            'subsystemCode': None,
            'serviceCode': None,
            'serviceVersion': None,
        },
        'userId': None,
        'id': None,
        'protocolVersion': None
    }

    def __init__(self, wsdl, client=None, service=None,
                 protocolVersion=4.0,
                 userId='?', id='?',
                 *args, **kwargs):
        self.security_server_url = wsdl

        client = client.split('/')
        assert len(client) == 4
        self.HEADER['client']['xRoadInstance'] = client[0]
        self.HEADER['client']['memberClass'] = client[1]
        self.HEADER['client']['memberCode'] = client[2]
        self.HEADER['client']['subsystemCode'] = client[3]

        service = service.split('/')
        assert len(service) == 6
        self.HEADER['service']['xRoadInstance'] = service[0]
        self.HEADER['service']['memberClass'] = service[1]
        self.HEADER['service']['memberCode'] = service[2]
        self.HEADER['service']['subsystemCode'] = service[3]
        self.HEADER['service']['serviceCode'] = service[4]
        self.HEADER['service']['serviceVersion'] = service[5]

        self.HEADER['protocolVersion'] = protocolVersion
        self.HEADER['userId'] = userId
        self.HEADER['id'] = id

        if '/wsdl' not in wsdl:
            wsdl = self._get_url_wsdl(wsdl)

        plugins = kwargs.get('plugins', [])
        plugins.append(XRoadPlugin(self))
        kwargs['plugins'] = plugins

        super().__init__(wsdl, *args, **kwargs)

        self.set_ns_prefix('xro', "http://x-road.eu/xsd/xroad.xsd")
        self.set_ns_prefix('iden', "http://x-road.eu/xsd/identifiers")

        self.set_default_soapheaders(self.HEADER)

    def _get_url_wsdl(self, url):
        params = {
            'xRoadInstance': self.HEADER['service'].get('xRoadInstance'),
            'memberClass': self.HEADER['service'].get('memberClass'),
            'memberCode': self.HEADER['service'].get('memberCode'),
            'serviceCode': self.HEADER['service'].get('serviceCode'),
            'subsystemCode': self.HEADER['service'].get('subsystemCode'),
            'version': self.HEADER['service'].get('serviceVersion')
        }
        return requests.Request(
            'GET', url + '/wsdl', params=params).prepare().url
