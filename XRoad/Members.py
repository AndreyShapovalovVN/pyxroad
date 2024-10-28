from dataclasses import dataclass


@dataclass
class Members:
    """
    This class is used to parse the memberPath and create a dictionary with the member details.
    """
    objectType: str
    memberPath: str
    xRoadInstance: str | None = None
    memberClass: str | None = None
    memberCode: str | None = None
    subsystemCode: str | None = None
    serviceCode: str | None = None
    serviceVersion: str | None = None

    def __post_init__(self):
        """
        This method is used to parse the memberPath and assign the values to the class variables.
        :return:
        """
        if self.memberPath:
            for iteration, val in enumerate(self.memberPath.split('/')):
                match iteration:
                    case 0:
                        self.xRoadInstance = val
                    case 1:
                        self.memberClass = val
                    case 2:
                        self.memberCode = val
                    case 3:
                        self.subsystemCode = val
                    case 4:
                        self.serviceCode = val
                    case 5:
                        self.serviceVersion = val

    @property
    def wsdl_path(self) -> str:
        """
        This method returns the wsdl path for the service.
        :return: str
        """
        if "SERVICE" in self.objectType:
            return f"xRoadInstance={self.xRoadInstance}/memberClass={self.memberClass}/memberCode={self.memberCode}/subsystemCode={self.subsystemCode}/serviceCode={self.serviceCode}/version={self.serviceVersion}"
        raise Exception("wsdl_path is only available for SERVICE objectType")

    def wsdl_url(self, ssu: str) -> str:
        """
        This method returns the wsdl url for the service.
        :param: ssu - url to securyt server
        :return: str
        """
        return f"{ssu}/{self.wsdl_path}"

    @property
    def member_dict(self) -> dict:
        """
        This method returns the member details in a dictionary format.
        :return: dict
        """
        return {
            'xRoadInstance': self.xRoadInstance,
            'memberClass': self.memberClass,
            'memberCode': self.memberCode,
            'subsystemCode': self.subsystemCode,
            'serviceCode': self.serviceCode,
            'serviceVersion': self.serviceVersion,
            'objectType': self.objectType
        }
