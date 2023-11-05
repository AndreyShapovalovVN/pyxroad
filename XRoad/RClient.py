import logging
import uuid
from urllib import parse

import requests

from .Uxp import Uxp, ADDR_FIELDS

_logger = logging.getLogger('XRoad')


class RClient(Uxp):

    def __init__(self, ssu: str, client: str, service: str, **kwargs):
        super().__init__(ssu, client, service, **kwargs)

        self.headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json',
            'Uxp-Client': client,
            'Uxp-Service': service,
            'Uxp-Id': uuid.uuid4().hex,
            'Uxp-UserId': {ADDR_FIELDS[i]: val for i, val in enumerate(client.split('/'))}.get('subsystemCode'),
            'Uxp-Issue': None,
            'Uxp-Purpose-Ids': None,
        }
        self.url = f'{ssu}/restapi'

        self.http_type = kwargs.get('type', 'GET')

    def request(self, **kwargs):
        super().request(**kwargs)

        _logger.debug('URL: %s', self.url)
        _logger.debug('Type: %s', self.http_type)
        _logger.debug('Headers: %s', self.headers)
        _logger.debug('Data: %s', kwargs)

        url = f'{self.url}?{parse.urlencode(kwargs)}' if kwargs else self.url
        response = requests.request(self.http_type, url, headers=self.headers)

        _logger.debug('Response status code: %s', response.status_code)
        _logger.debug(response.content)

        if response.status_code == 200:
            return response.json()
        else:
            return {"status_code": response.status_code, "content": response.content}

    @property
    def id(self):
        return self.headers.get('Uxp-Id')

    @id.setter
    def id(self, value):
        self.headers.update({'Uxp-Id': value})
        _logger.debug(f'Set (id: {value})')

    @property
    def user_id(self):
        return self.headers.get('Uxp-UserId')

    @user_id.setter
    def user_id(self, value):
        self.headers.update({'Uxp-UserId': value})
        _logger.debug(f'Set (user_id: {value})')

    @property
    def issue(self):
        return self.headers.get('Uxp-Issue')

    @issue.setter
    def issue(self, value):
        self.headers.update({'Uxp-Issue': value})
        _logger.debug(f'Set (Issue: {value})')

    @property
    def purposeID(self) -> str:
        return self.headers.get('Uxp-Purpose-Ids')


    @purposeID.setter
    def purposeID(self, value: str):
        self.headers.update({"Uxp-Purpose-Ids": value})
        _logger.debug(f'Set (purposeID: {value})')
