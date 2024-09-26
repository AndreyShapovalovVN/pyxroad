import logging
import os
import tempfile
import uuid
from urllib import parse

import requests
from lxml import etree
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


class XClient(Client):
    _version = 4.0

    def __init__(self, ssu, client, service, transport=None, hack_wsdl=False, *args, **kwargs):
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

        if hack_wsdl:
            wsdl = _hack_wsdl(_get_wsdl_url(ssu, service))
        else:
            wsdl = _get_wsdl_url(ssu, service)

        super().__init__(
            wsdl,
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


def _hack_wsdl(path):
    _logger.info(f"Hacking WSDL from {path}")
    response = requests.get(path)
    if response.status_code != 200:
        _logger.error(f"Failed to retrieve WSDL from {path}")
        raise Exception(f"Failed to retrieve WSDL from {path}")
    _logger.debug(f"Response from {path}: {response.content}")
    root = etree.fromstring(response.content)
    for definitions in root:
        if "portType" in definitions.tag:
            for portType in definitions:
                if "operation" in portType.tag:
                    for operation in portType:
                        if "input" in operation.tag:
                            continue
                        if "output" in operation.tag:
                            continue
                        _logger.debug(f"Removing {definitions.tag} -> {portType.tag} -> {operation.tag}")
                        portType.remove(operation)

    tmpdirname = tempfile.TemporaryDirectory().name
    os.mkdir(tmpdirname)
    _logger.debug(f'created temporary directory: {tmpdirname}')
    with open(f'{tmpdirname}/wsdl.xml', 'wb') as f:
        f.write(etree.tostring(root, pretty_print=True))
    return f'{tmpdirname}/wsdl.xml'
