# -*- coding: utf-8 -*-
#Python 3.5.x
#utf8编码

from ._okcoin import OKCOIN_BTC
from ._okcoin import OKCOIN_ETH

class OKCOIN_BTC_CNY(OKCOIN_BTC):
    def __init__(self):
        super().__init__("CNY", "okcoinBtcCny")
        
class OKCOIN_ETH_CNY(OKCOIN_ETH):
    def __init__(self):
        super().__init__("CNY", "okcoinEthCny")

