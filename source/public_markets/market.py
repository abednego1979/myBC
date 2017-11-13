# -*- coding: utf-8 -*-
#Python 3.5.x
#utf8编码

import time
import config
import logging
import sys
from utils import log_exception
import myGlobal

class Market(object):
    def __init__(self, currency):
        self.name = self.__class__.__name__
        self.currency = currency
        self.tradeinfo_updated_time = 0
        self.update_rate = 60
        
        #init proxy
        proxies={}       
        if myGlobal.userChooseProxySet=='on':
            #代理信息加密存储，这里先要解密
            passKey=input('The PROXY is on, Right?(Y/N)')
            assert len(passKey)==16 or len(passKey)==24 or len(passKey)==32
        
            ciphertext = config.config_proxy_info
            ciphertext = base64.b64decode(ciphertext)
            temp_config_proxy = AES.new(passKey, AES.MODE_CBC, b'0000000000000000').decrypt(ciphertext)
            temp_config_proxy = str(temp_config_proxy, encoding = "utf-8").rstrip(' ')
            assert temp_config_proxy.endswith('MAGIC')
            temp_config_proxy=json.loads(temp_config_proxy[:-len('MAGIC')])            

            a=temp_config_proxy['user']
            b=temp_config_proxy['password']
            if temp_config_proxy['ip_http']:
                proxies['http']="http://"+a+":"+b+"@"+temp_config_proxy['ip_http']
            if temp_config_proxy['ip_https']:
                proxies['https']="http://"+a+":"+b+"@"+temp_config_proxy['ip_https']
        self.proxies=proxies
        

    def get_tradeinfo(self):
        timediff = time.time() - self.tradeinfo_updated_time
        if timediff > self.update_rate:
            self.ask_update_tradeinfo()
        timediff = time.time() - self.tradeinfo_updated_time
        if timediff > config.market_expiration_time:
            logging.warn('Market: %s order book is expired' % self.name)
            self.depth = None
            self.detail = None
            self.quotation = None
        return {'depth' : self.depth}

    def ask_update_tradeinfo(self):
        try:
            self.update_depth()#买卖盘深度
            #self.update_detail()#实时成交数据
            #self.update_quotation()#行情
            self.tradeinfo_updated_time = time.time()
        except Exception as e:
            logging.error("Can't update market: %s - %s" % (self.name, str(e)))
            log_exception(logging.DEBUG)
            
    def get_ticker(self):
        tradeinfo = self.get_tradeinfo()
        return tradeinfo

    ## Abstract methods
    def update_depth(self):
        pass

    def buy(self, price, amount):
        pass

    def sell(self, price, amount):
        pass
