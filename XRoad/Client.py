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

    def __init__(self, ssu, client, service, *args, **kwargs):
        self.response = None

        if not service:
            raise Exception('service - required')
        if not client:
            raise Exception('client - required')

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
        _logger.debug('wsdl url(%s)', wsdl)

        service['objectType'] = 'SERVICE'
        client['objectType'] = 'SUBSYSTEM'

        # plugins = kwargs.get('plugins') or []
        # plugins.append(XRoadPlugin(self))
        # kwargs['plugins'] = plugins
        # _logger.debug('Plugins (%s)', plugins)

        super().__init__(wsdl, *args, **kwargs)

        self.set_ns_prefix('xro', "http://x-road.eu/xsd/xroad.xsd")
        self.set_ns_prefix('iden', "http://x-road.eu/xsd/identifiers")

        self.set_default_soapheaders(
            {
                'client': client,
                'service': service,
                'userId': client.get('subsystemCode'),
                'id': '0',
                'protocolVersion': '4.0',
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

    def _element(self, body, responce, parrent, iter=0, report=True):

        _logger.debug('Recursion depth %s', iter)

        if iter == 1000:
            _logger.error('Emergency exit from recursion')
            return responce
        iter += 1
        responce.update({parrent: {}})

        for name, element in body.type.elements:
            if hasattr(element.type, 'elements_nested'):

                responce[parrent].update({
                    name: dict(
                        element.type.elements_nested[0][1].default_value)
                })

                self._element(
                    element, responce[parrent], name, iter=iter, report=report
                )
            else:
                if report:
                    responce[parrent].update({
                        name: {
                            'type': element.type.name,
                            'is_optional': element.is_optional,
                            'max_occurs': element.max_occurs,
                            'min_occurs': element.min_occurs,
                            'nillable': element.nillable,
                        }
                    })
        return responce

    def wsdl_elements(self, put, report=True):
        if put not in ('input', 'output'):
            raise ValueError("ValueError ('input', 'output')")

        element = {}
        for service in self.wsdl.services.values():
            for port in service.ports.values():
                for operation in port.binding._operations.values():
                    element = self._element(
                        operation.__dict__[put].body,
                        {},
                        put,
                        report
                    )
        return element
