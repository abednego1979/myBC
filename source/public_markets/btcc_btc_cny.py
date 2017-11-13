# -*- coding: utf-8 -*-
#Python 3.5.x
#utf8编码

from ._btcc import BTCC_BTC
from ._btcc import BTCC_ETH

class BTCC_BTC_CNY(BTCC_BTC):
    def __init__(self):
        super().__init__("CNY", "btccBtcCny")


class BTCC_ETH_CNY(BTCC_ETH):
    def __init__(self):
        super().__init__("CNY", "btccEthCny")