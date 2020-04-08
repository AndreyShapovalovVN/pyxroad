**X-Road (Trembita) client**
============================

:Forked from: https://github.com/City-of-Helsinki/pyxroad
:Version: 1.1.
:Web: https://trembita.gov.ua
:Download: https://github.com/AndreyShapovalovVN/pyxroad.git
:Source: https://github.com/AndreyShapovalovVN/pyxroad.git
:Doc: https://trembita.gov.ua/storage/app/media/uploaded-files/Tutorial_Member_20190419_dev.pdf
:Keywords: x-road, xroad, trembita, python

**What python version is supported?**
-------------------------------------

- Python 3.6

**Installation From github**
----------------------------
::

    $ pip install git+https://github.com/AndreyShapovalovVN/pyxroad.git#egg=XRoad

**Using:**
----------
::

    import XRoad
    import logging
    import sys
    from zeep.plugins import HistoryPlugin

    history = HistoryPlugin()

    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    _logger = logging.getLogger('XRoad')

    c = XRoad.Client(
        "http://security_server",
        client='SEVDEIR-TEST/GOV/00013480/100001',
        serviсe='SEVDEIR-TEST/GOV/00032684/MIA_prod/CheckPassportStatus/v0.1',
        protocolVersion=4.0,
        userId='?',
        id='?',
        plugins=[history])

    try:
        response = c.request(PasNumber='', PasSerial='')
    except Exception as err:
        _logger.error(err)
    else:
        _logger.info(response['body'])

