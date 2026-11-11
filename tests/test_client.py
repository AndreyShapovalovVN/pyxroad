from unittest.mock import Mock

import pytest
from lxml import etree
from zeep.transports import Transport

from XRoad.client import XClient

XROAD = "http://x-road.eu/xsd/xroad.xsd"
SOAP = "http://schemas.xmlsoap.org/soap/envelope/"


def make_client(declare_issue=False):
    names = ["protocolVersion", "userId", "service", "client", "id"]
    if declare_issue:
        names.append("issue")
    elements = "".join(
        f'<xs:element name="{name}" type="xs:string"/>'
        for name in names
        if name not in ("service", "client")
    )
    for name in ("service", "client"):
        fields = ["xRoadInstance", "memberClass", "memberCode", "subsystemCode"]
        if name == "service":
            fields += ["serviceCode", "serviceVersion"]
        elements += f'<xs:element name="{name}"><xs:complexType><xs:sequence>'
        elements += "".join(
            f'<xs:element name="{field}" type="xs:string" minOccurs="0"/>'
            for field in fields
        )
        elements += '</xs:sequence><xs:attribute name="objectType" type="xs:string"/></xs:complexType></xs:element>'
    parts = "".join(f'<part name="{name}" element="tns:{name}"/>' for name in names)
    headers = "".join(
        f'<soap:header message="tns:Headers" part="{name}" use="literal"/>'
        for name in names
    )
    wsdl = f'''<definitions xmlns="http://schemas.xmlsoap.org/wsdl/"
        xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
        xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:tns="{XROAD}"
        targetNamespace="{XROAD}">
      <types><xs:schema targetNamespace="{XROAD}" elementFormDefault="qualified">
        {elements}<xs:element name="lookup" type="xs:string"/>
      </xs:schema></types>
      <message name="Headers">{parts}</message>
      <message name="Input"><part name="body" element="tns:lookup"/></message>
      <portType name="Port"><operation name="lookup"><input message="tns:Input"/></operation></portType>
      <binding name="Binding" type="tns:Port">
        <soap:binding style="document" transport="http://schemas.xmlsoap.org/soap/http"/>
        <operation name="lookup"><soap:operation soapAction="lookup"/>
          <input><soap:body use="literal"/>{headers}</input>
        </operation>
      </binding>
      <service name="Service"><port name="Port" binding="tns:Binding">
        <soap:address location="http://example.test/service"/>
      </port></service>
    </definitions>'''
    transport = Transport()
    transport.load = Mock(return_value=wsdl.encode())
    return XClient(
        "http://example.test",
        "INSTANCE/CLASS/MEMBER/SUBSYSTEM",
        "INSTANCE/CLASS/MEMBER/SUBSYSTEM/lookup/v1",
        transport=transport,
    )


@pytest.mark.parametrize("declare_issue", [False, True])
def test_issue_serializes_with_or_without_wsdl_declaration(declare_issue):
    client = make_client(declare_issue)
    client.issue = "document <123> & case"
    envelope = client.create_message(
        client.service, "lookup", "payload", _soapheaders=client._default_soapheaders
    )
    # Round-trip XML to also check escaping and the exact namespace.
    envelope = etree.fromstring(etree.tostring(envelope))
    header = envelope.find(f"{{{SOAP}}}Header")
    assert [node.text for node in header.findall(f"{{{XROAD}}}issue")] == [client.issue]
    assert header.find(f"{{{XROAD}}}id").text == client.id
    assert header.find(f"{{{XROAD}}}service/{{{XROAD}}}serviceCode").text == "lookup"


def test_issue_can_be_updated_and_cleared():
    client = make_client()
    for value in (None, "first", "second", "", None):
        client.issue = value
        envelope = client.create_message(
            client.service,
            "lookup",
            "payload",
            _soapheaders=client._default_soapheaders,
        )
        nodes = envelope.findall(f"{{{SOAP}}}Header/{{{XROAD}}}issue")
        assert len(nodes) == (0 if value is None else 1)
        if nodes:
            assert nodes[0].text == value


def test_per_call_issue_takes_precedence():
    client = make_client(declare_issue=True)
    client.issue = "default"
    envelope = client.create_message(
        client.service, "lookup", "payload", _soapheaders={"issue": "override"}
    )
    nodes = envelope.findall(f"{{{SOAP}}}Header/{{{XROAD}}}issue")
    assert [node.text for node in nodes] == ["override"]
    assert client.issue == "default"


def test_request_sends_issue_without_wsdl_declaration():
    from requests import Response

    client = make_client()
    response = Response()
    response.status_code = 202
    response._content = b""
    client.transport.post_xml = Mock(return_value=response)
    client.issue = "case-123"
    client.request(xroad_id="request-123", value="payload")
    envelope = client.transport.post_xml.call_args.args[1]
    header = envelope.find(f"{{{SOAP}}}Header")
    assert header.find(f"{{{XROAD}}}issue").text == "case-123"
    assert header.find(f"{{{XROAD}}}id").text == "request-123"


@pytest.mark.parametrize("proxy_kind", ["default", "bind", "create_service"])
def test_additional_headers_merge_without_mutating_defaults(proxy_kind):
    from requests import Response

    client = make_client()
    defaults = dict(client._default_soapheaders, trackingId="default", omitted="value")
    client.set_default_soapheaders(defaults)
    xml = etree.Element("{urn:custom}context", role="caller")
    etree.SubElement(xml, "{urn:custom}code").text = "123"
    response = Response()
    response.status_code = 202
    response._content = b""
    client.transport.post_xml = Mock(return_value=response)
    proxy = client.service
    if proxy_kind == "bind":
        proxy = client.bind()
    elif proxy_kind == "create_service":
        proxy = client.create_service(
            f"{{{XROAD}}}Binding", "http://example.test/other"
        )
    proxy.lookup(
        "payload",
        _soapheaders={
            "trackingId": "override & <value>",
            "omitted": None,
            "enabled": True,
            "count": 0,
            "{urn:custom}context": xml,
        },
    )
    header = client.transport.post_xml.call_args.args[1].find(f"{{{SOAP}}}Header")
    assert header.find(f"{{{XROAD}}}trackingId").text == "override & <value>"
    assert header.find(f"{{{XROAD}}}omitted") is None
    assert header.find(f"{{{XROAD}}}enabled").text == "true"
    assert header.find(f"{{{XROAD}}}count").text == "0"
    assert header.find("{urn:custom}context/{urn:custom}code").text == "123"
    assert header.find("{urn:custom}context").get("role") == "caller"
    assert defaults["trackingId"] == "default"
    assert defaults["omitted"] == "value"
    assert xml.getparent() is None


def test_declared_header_validation_is_preserved():
    client = make_client()
    with pytest.raises(TypeError, match="unexpected keyword argument"):
        client.create_message(
            client.service,
            "lookup",
            "payload",
            _soapheaders={
                "service": {"invalidField": "value"},
                "extra": "value",
            },
        )


def test_complex_extension_requires_explicit_xml():
    client = make_client()
    with pytest.raises(TypeError, match="scalar or an lxml element"):
        client.create_message(
            client.service,
            "lookup",
            "payload",
            _soapheaders={
                "extra": {"ambiguous": "value"},
            },
        )


def test_only_omitted_extension_does_not_reach_zeep_as_dict():
    from requests import Response

    client = make_client()
    client.set_default_soapheaders({})
    response = Response()
    response.status_code = 202
    response._content = b""
    client.transport.post_xml = Mock(return_value=response)
    client.service.lookup("payload", _soapheaders={"extra": None})
    assert client.transport.post_xml.call_args.args[1].find(f"{{{SOAP}}}Header") is None
