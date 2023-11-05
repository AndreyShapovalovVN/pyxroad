import logging
from .XClient import XClient
from .RClient import RClient

_logger = logging.getLogger('XRoad')


def Client(protokol, *args, **kwargs):
    if protokol == 'SOAP':
        return XClient(*args, **kwargs)
    elif protokol == 'REST':
        return RClient(*args, **kwargs)
    else:
        raise ValueError('Supported protocols only SOAP and REST')
