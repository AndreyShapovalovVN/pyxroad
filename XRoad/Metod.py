import logging

import requests
from lxml import etree

_logger = logging.getLogger('XRoad-Metods')

HEADERS = {'content-type': "text/xml"}
DEFAULT_TIMEOUT = 5.0


class RequestMetod:
    _expr = "//*[local-name() = $parent]/*[local-name() = $name]"
    _xml = etree.fromstring('''
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" 
                          xmlns:xro="http://x-road.eu/xsd/xroad.xsd" 
                          xmlns:iden="http://x-road.eu/xsd/identifiers">
           <soapenv:Header>
              <xro:client iden:objectType="SUBSYSTEM">
                    <iden:xRoadInstance/>
                    <iden:memberClass/>
                    <iden:memberCode/>
                    <iden:subsystemCode/>
              </xro:client>
              <xro:service iden:objectType="SERVICE">
                    <iden:xRoadInstance/>
                    <iden:memberClass/>
                    <iden:memberCode/>
                    <iden:subsystemCode/>
                    <iden:serviceCode/>
              </xro:service>
              <xro:userId>0</xro:userId>
              <xro:id>0</xro:id>
              <xro:protocolVersion>4.0</xro:protocolVersion>
           </soapenv:Header>
           <soapenv:Body/>
        </soapenv:Envelope>
''')

    def __init__(self, client: dict, service: dict, method: str = 'listMethods'):
        self.set_key(parent='client', name='xRoadInstance', value=client.get('xRoadInstance'))
        self.set_key(parent='client', name='memberClass', value=client.get('memberClass'))
        self.set_key(parent='client', name='memberCode', value=client.get('memberCode'))
        self.set_key(parent='client', name='subsystemCode', value=client.get('subsystemCode'))
        self.set_key(parent='service', name='xRoadInstance', value=service.get('xRoadInstance'))
        self.set_key(parent='service', name='memberClass', value=service.get('memberClass'))
        self.set_key(parent='service', name='memberCode', value=service.get('memberCode'))
        self.set_key(parent='service', name='subsystemCode', value=service.get('subsystemCode'))
        self.set_key(parent='service', name='serviceCode', value=service.get('serviceCode'))
        self.set_key(parent='service', name='serviceCode', value=method)

    @property
    def xml_request(self) -> str:
        return etree.tostring(self._xml)

    @property
    def xml(self) -> etree:
        return self._xml

    def get_key(self, parent: str, name: str) -> list:
        return self.xml.xpath(self._expr, parent=parent, name=name)

    def set_key(self, parent: str, name: str, value: str):
        self.get_key(parent, name)[0].text = value


class Metod:
    '''
    Create list methods UXP
    '''
    EXPR = '//*[local-name() = $lmr]/*[local-name() = $service]'
    _response = None
    _fault = None
    _service = None
    _url = []

    def __init__(self, ip, client=None, service=None, method='listMethods'):
        self.ip = ip
        self.method = method
        self.payload = RequestMetod(
            client=client, service=service, method=method)

    @property
    def fault(self):
        if isinstance(self._fault, etree._Element):
            return {
                'faultcode': self._fault.find('faultcode').text,
                'faultstring': self._fault.find('faultstring').text,
            }
        return None

    @fault.setter
    def fault(self, value):
        if value:
            self._fault = value[0]
        _logger.debug(self._fault)

    @property
    def service(self):
        if self._service:
            for method in self._service:
                yield self._todict(method)

    @service.setter
    def service(self, value):
        self._service = value

    @staticmethod
    def _todict(xml):
        def get_text(tag):
            if tag:
                return tag[0].text
            return None

        expr = '*[local-name() = $name]'
        return {
            'xRoadInstance': get_text(xml.xpath(expr, name='xRoadInstance')),
            'memberClass': get_text(xml.xpath(expr, name='memberClass')),
            'memberCode': get_text(xml.xpath(expr, name='memberCode')),
            'subsystemCode': get_text(xml.xpath(expr, name='subsystemCode')),
            'serviceCode': get_text(xml.xpath(expr, name='serviceCode')),
            'serviceVersion': get_text(xml.xpath(expr, name='serviceVersion')),
        }

    @property
    def response(self):
        return self._response

    @response.setter
    def response(self, value):
        self._response = value
        self.fault = value.xpath('//*[local-name() = $fault]', fault='Fault')
        self.service = value.xpath(
            self.EXPR, lmr='{}Response'.format(self.method), service='service')

    def get_content(self):
        _logger.debug(self.payload.xml.decode('utf8'))
        am = requests.post(
            'http://%s' % self.ip,
            data=self.payload.xml,
            headers=HEADERS, )
        _logger.debug(am.content)
        if not am.content:
            raise Exception('Empty content')
        try:
            self.response = etree.fromstring(am.content)
        except Exception as err:
            _logger.error(err)
            raise err
        else:
            return self
