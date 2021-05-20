import logging

from lxml import etree
from zeep.transports import Transport

_logger = logging.getLogger('DRACTransport')


class DRACTransport(Transport):
    def post_xml(self, address, envelope, headers):
        message = etree.tostring(
            envelope, pretty_print=True, xml_declaration=True, encoding="utf-8"
        ).decode('utf-8')

        _logger.debug(f'Source: \n {message}')
        drac_message = ''
        for line in message.splitlines():
            drac_message += line
            if 'iden:' not in line:
                drac_message += '\n'
        _logger.debug(f'Modified: \n {drac_message}')

        return self.post(address, drac_message.encode('utf-8'), headers)
