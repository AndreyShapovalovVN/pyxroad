import pytest
import requests
from unittest.mock import patch, MagicMock
from XRoad.fixBagInWSDL import _hack_wsdl


def hack_wsdl_success():
    wsdl_content = b"""<definitions>
        <service name="OldServiceName"/>
        <portType>
            <operation>
                <input/>
                <output/>
            </operation>
            <operation>
                <input/>
            </operation>
        </portType>
    </definitions>"""

    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = wsdl_content
        mock_get.return_value = mock_response

        result = _hack_wsdl('http://example.com/wsdl', 'NewServiceName')
        assert 'wsdl.xml' in result


def hack_wsdl_invalid_url():
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with pytest.raises(Exception, match="Failed to retrieve WSDL from http://invalid-url.com/wsdl"):
            _hack_wsdl('http://invalid-url.com/wsdl', 'NewServiceName')


def hack_wsdl_no_service_tag():
    wsdl_content = b"""<definitions>
        <portType>
            <operation>
                <input/>
                <output/>
            </operation>
        </portType>
    </definitions>"""

    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = wsdl_content
        mock_get.return_value = mock_response

        result = _hack_wsdl('http://example.com/wsdl', 'NewServiceName')
        assert 'wsdl.xml' in result


def hack_wsdl_no_operations():
    wsdl_content = b"""<definitions>
        <service name="OldServiceName"/>
        <portType>
        </portType>
    </definitions>"""

    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = wsdl_content
        mock_get.return_value = mock_response

        result = _hack_wsdl('http://example.com/wsdl', 'NewServiceName')
        assert 'wsdl.xml' in result