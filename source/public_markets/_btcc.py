# -*- coding: utf-8 -*-
#Python 3.5.x
#utf8编码

import sys
import requests
import json
from .market import Market

class BTCC_BTC(Market):
    def __init__(self, currency, symbol):
        super().__init__(currency)
        self.symbol = symbol
        self.update_rate = 30
        
    #实时行情
    def update_quotation(self):
        requests.packages.urllib3.disable_warnings()
        r = requests.get('https://data.btcchina.com/data/ticker?market=btccny', proxies=self.proxies, verify=False)
        
        quotation = json.loads(r.content.decode('utf8'))
        self.quotation = quotation        
        pass
    
    #买卖盘实时成交数据 
    def update_detail(self):
        requests.packages.urllib3.disable_warnings()
        r = requests.get('https://data.btcchina.com/data/historydata?limit=60', proxies=self.proxies, verify=False)
        
        detail = json.loads(r.content.decode('utf8'))
        self.detail = detail
        pass
        
    #深度数据
    def update_depth(self):
        requests.packages.urllib3.disable_warnings()
        r = requests.get('https://data.btcchina.com/data/orderbook?limit=150', proxies=self.proxies, verify=False)
        
        depth = json.loads(r.content.decode('utf8'))
        self.depth = self.format_depth(depth)
        pass

    def sort_and_format(self, l, reverse=False):
        l.sort(key=lambda x: float(x[0]), reverse=reverse)
        r = []
        for i in l:
            r.append({'price': float(i[0]), 'amount': float(i[1])})
        return r

    def format_depth(self, depth):
        bids = self.sort_and_format(depth['bids'], True)
        asks = self.sort_and_format(depth['asks'], False)
        return {'asks': asks, 'bids': bids}


class BTCC_ETH(Market):
    def __init__(self, currency, symbol):
        super().__init__(currency)
        self.symbol = symbol
        self.update_rate = 30