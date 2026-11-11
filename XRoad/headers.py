"""Serialize extension SOAP headers without changing the operation's schema."""

from copy import deepcopy
from decimal import Decimal

from lxml import etree
from zeep.proxy import OperationProxy, ServiceProxy

XROAD_NAMESPACE = "http://x-road.eu/xsd/xroad.xsd"


def serialize_headers(binding, operation_name, headers):
    if not isinstance(headers, dict):
        return headers

    message = binding.get(operation_name).input
    declared = dict(message.header.type.elements) if message.header is not None else {}
    extra = {name: value for name, value in headers.items() if name not in declared}
    if not extra:
        return headers

    known = {name: value for name, value in headers.items() if name in declared}
    rendered = message._serialize_header(known, {})
    result = list(rendered) if rendered is not None else []
    for name, value in extra.items():
        if value is None:
            continue
        tag = str(name) if str(name).startswith("{") else f"{{{XROAD_NAMESPACE}}}{name}"
        if isinstance(value, etree._Element):
            if value.tag != tag:
                raise ValueError(
                    f"SOAP header {name!r} does not match XML element {value.tag!r}"
                )
            result.append(deepcopy(value))
            continue
        if not isinstance(value, (str, bool, int, float, Decimal)):
            raise TypeError(
                f"Undeclared SOAP header {name!r} requires a scalar or an lxml element"
            )
        element = etree.Element(tag)
        element.text = str(value).lower() if isinstance(value, bool) else str(value)
        result.append(element)
    return result


class XRoadOperationProxy(OperationProxy):
    def __call__(self, *args, **kwargs):
        headers = self._merge_soap_headers(kwargs.get("_soapheaders"))
        kwargs["_soapheaders"] = serialize_headers(
            self._proxy._binding, self._op_name, headers
        )
        return self._proxy._binding.send(
            self._proxy._client,
            self._proxy._binding_options,
            self._op_name,
            args,
            kwargs,
        )


class XRoadServiceProxy(ServiceProxy):
    def __init__(self, client, binding, **binding_options):
        super().__init__(client, binding, **binding_options)
        self._operations = {
            name: XRoadOperationProxy(self, name) for name in binding.all()
        }

    @classmethod
    def wrap(cls, proxy):
        if proxy is None:
            return None
        return cls(proxy._client, proxy._binding, **proxy._binding_options)
