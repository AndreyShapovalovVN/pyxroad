import logging
from dataclasses import dataclass

_logger = logging.getLogger(__name__)


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
        _logger.debug(f"Members init: {self.memberPath}")
        if self.memberPath:
            for iteration, val in enumerate(self.memberPath.split("/")):
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
            _path = []
            for key, value in self.member_dict.items():
                if not value:
                    _logger.debug(f"Skipping {key} as value is None")
                    continue
                if key in ("objectType", "memberPath"):
                    _logger.debug(f"Skipping {key}")
                    continue
                if value is None:
                    _logger.debug(f"Skipping {key}")
                    continue
                if "serviceVersion" in key:
                    _logger.debug(f"Adding version={value}")
                    _path.append(f"version={value}")
                    continue
                _logger.debug(f"Adding {key}={value}")
                _path.append(f"{key}={value}")
            _logger.info(f"wsdl path: {_path[:-1]}")
            return "&".join(_path)
        raise ValueError("wsdl_path is only available for SERVICE objectType")

    def wsdl_url(self, ssu: str) -> str:
        """
        This method returns the wsdl url for the service.
        :param: ssu - url to securyt server
        :return: str
        """
        _logger.info(f"Generating wsdl url for {ssu}")
        return f"{ssu}/wsdl?{self.wsdl_path}"

    @property
    def member_dict(self) -> dict:
        """
        This method returns the member details in a dictionary format.
        :return: dict
        """
        _logger.info("Returning member details as dictionary")
        r = {}
        if self.xRoadInstance:
            r["xRoadInstance"] = self.xRoadInstance
        if self.memberClass:
            r["memberClass"] = self.memberClass
        if self.memberCode:
            r["memberCode"] = self.memberCode
        if self.subsystemCode:
            r["subsystemCode"] = self.subsystemCode
        if self.serviceCode:
            r["serviceCode"] = self.serviceCode
        if self.serviceVersion:
            r["serviceVersion"] = self.serviceVersion
        if self.objectType:
            r["objectType"] = self.objectType

        return r
