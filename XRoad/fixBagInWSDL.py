import logging
import os
import tempfile
import requests
from lxml import etree

_logger = logging.getLogger(__name__)


def _hack_wsdl(path: str, service: str) -> str:
    """
    :param path: url to WSDL
    :param service: service name
    :return: path to temporary WSDL file
    """
    _logger.info(f"Hacking WSDL from {path}")
    response = requests.get(path)
    if response.status_code != 200:
        _logger.error(f"Failed to retrieve WSDL from {path}")
        raise Exception(f"Failed to retrieve WSDL from {path}")
    _logger.debug(f"Response from {path}: {response.content}")  # type: ignore
    root = etree.fromstring(response.content)
    for definitions in root:
        if "service" in definitions.tag:
            definitions.attrib["name"] = service
        if "portType" in definitions.tag:
            for portType in definitions:
                if "operation" in portType.tag:
                    for operation in portType:
                        if operation.tag not in ("input", "output"):
                            _logger.debug(
                                f"Removing {definitions.tag} -> {portType.tag} -> {operation.tag}"
                            )
                            portType.remove(operation)

    tmpdirname = tempfile.mkdtemp()
    with open(os.path.join(tmpdirname, "wsdl.xml"), "wb") as f:
        f.write(etree.tostring(root, pretty_print=True))

    return os.path.join(tmpdirname, "wsdl.xml")
