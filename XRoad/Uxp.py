from abc import ABC, abstractmethod
from urllib import parse

ADDR_FIELDS = (
    'xRoadInstance',
    'memberClass',
    'memberCode',
    'subsystemCode',
    'serviceCode',
    'serviceVersion')


class Uxp(ABC):
    _version = None

    def __init__(self, ssu: str, client: str, service: str, **kwargs):
        if not service:
            raise Exception('service - required')
        if not client:
            raise Exception('client - required')

        self._ssu = ssu
        self.service = service
        self.client = client

    @property
    def service(self) -> dict:
        return self._service

    @service.setter
    def service(self, value: str):
        self._service = {ADDR_FIELDS[i]: val for i, val in enumerate(value.split('/'))}

    @property
    def client(self) -> dict:
        return self._client

    @client.setter
    def client(self, value: str):
        self._client = {ADDR_FIELDS[i]: val for i, val in enumerate(value.split('/'))}

    def request(self, **kwargs) -> dict:
        if kwargs.get('xroad_id'):
            self.id = kwargs.get('xroad_id')
            del kwargs['xroad_id']

        if kwargs.get('xroad_issue'):
            self.issue = kwargs.get('xroad_issue')
            del kwargs['xroad_issue']

        if kwargs.get('xroad_purposeID'):
            self.purposeID = kwargs.get('xroad_purposeID')
            del kwargs['xroad_purposeID']

    @property
    def get_wsdl_url(self):
        s = self._service.copy()
        if s.get('objectType'):
            del s['objectType']
        if s.get('serviceVersion'):
            s.update({'version': s.get('serviceVersion')})
            del s['serviceVersion']
        u = parse.urlparse(self._ssu)
        return parse.urlunparse(u._replace(path='wsdl', query=parse.urlencode(s)))

    @property
    @abstractmethod
    def id(self) -> str:
        pass

    @id.setter
    @abstractmethod
    def id(self, value: str):
        pass

    @property
    @abstractmethod
    def user_id(self) -> str:
        pass

    @user_id.setter
    @abstractmethod
    def user_id(self, value: str):
        pass

    @property
    @abstractmethod
    def issue(self) -> str:
        pass

    @issue.setter
    @abstractmethod
    def issue(self, value: str):
        pass

    @property
    @abstractmethod
    def purposeID(self) -> str:
        pass

    @purposeID.setter
    @abstractmethod
    def purposeID(self, value: str):
        pass
