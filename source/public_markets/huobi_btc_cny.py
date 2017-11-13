# -*- coding: utf-8 -*-
#Python 3.5.x
#utf8编码

from ._huobi import HUOBI_BTC
from ._huobi import HUOBI_ETH

class HUOBI_BTC_CNY(HUOBI_BTC):
    def __init__(self):
        super().__init__("CNY", "huobiBtcCny")
        
        
class HUOBI_ETH_CNY(HUOBI_ETH):
    def __init__(self):
        super().__init__("CNY", "huobiEthCny")
