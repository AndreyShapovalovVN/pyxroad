**X-Road (Trembita) client**
============================

:Forked from: https://github.com/City-of-Helsinki/pyxroad
:Version: 1.3.1
:Web: https://trembita.gov.ua
:Download: https://github.com/AndreyShapovalovVN/pyxroad.git
:Source: https://github.com/AndreyShapovalovVN/pyxroad.git
:Doc: https://trembita.gov.ua/storage/app/media/uploaded-files/Tutorial_Member_20190419_dev.pdf
:Keywords: x-road, xroad, trembita, python

**What python version is supported?**
-------------------------------------

- Python 3.8

**Installation From github**
----------------------------
::

    $ pip install git+https://github.com/AndreyShapovalovVN/pyxroad.git#egg=XRoad

**Using:**
----------
::

    from XRoad import XClient, SqliteCache, Transport
    import logging
    import sys


    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    _logger = logging.getLogger('XRoad')

    c = XClient(
        "http://security_server",
        client='SEVDEIR-TEST/GOV/00013480/100001',
        serviсe='SEVDEIR-TEST/GOV/00032684/MIA_prod/CheckPassportStatus/v0.1',
        hack_wsdl=True,  # Fixing Bag from WSDL in Trembita. Optionals, default False
        userId = '0123456789',  # Optionals
        transport=Transport(cache=SqliteCache(path='./sqlite.db', timeout=60)),  # Optionals, default cache inmemory
    )

    c.userId = '0123456789'  # Optionals, default {Client subsystemCode}
    c.id = 'ABCD123456'  # Optionals, default uuid.uuid4().hex

    try:
        response = c.request(
            xroad_id='ABCD123456',  # Optionals priority
            PasNumber='',
            PasSerial=''
        )
    except Exception as err:
        _logger.error(err)
    else:
        _logger.info(response)

