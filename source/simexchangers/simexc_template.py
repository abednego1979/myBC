#*- coding: utf-8 -*-
#Python 3.5.x
#utf8编码
import sys
import logging
import traceback
import json
from .simexchanger import Simexchanger
import myGlobal
import config


#实现的阶梯价格交易模拟


class simexc_Template_Actor():
    
    def __init__(self, Macket, T, N):   #T:时间均线的时间长度，N:买卖点百分比阈值
        
        self.LoggerPrefixString="<simexcTemplate:%s,%f>" % (json.dumps(self.Mackets), self.threshold)
        
        #define private value       
        pass
    
    def selfLogger(self, level, OutString):
        try:
            if level=='info':
                myGlobal.logger.info(self.LoggerPrefixString+OutString)
            elif level=='debug':
                myGlobal.logger.debug(self.LoggerPrefixString+OutString)
            elif level=='error':
                myGlobal.logger.error(self.LoggerPrefixString+OutString)
        except Exception as err:
            print (err)
            print(traceback.format_exc())
            myGlobal.logger.error("ERROR: %s, %d" % (__file__, sys._getframe().f_lineno)) 
    
    def getCurProperty(self, price):
        #calc current Property
        temp=0.0
        return temp

    def newPriceProc(self, tradeinfo):
        #proc code for new tradeinfo
        pass


class simexc_Template(Simexchanger):
    actors=[]
        
    def __init__(self):
        #这里初始化Actor
        self.actors=[]
        
        super(simexc_Template, self).__init__()

    #准备工作
    def begin(self):
        pass

    #收尾工作
    def end(self):
        pass
    
    def simExchanger(self, tradeinfo):
        for actor in self.actors:
            try:
                actor.newPriceProc(tradeinfo)
            except Exception as err:
                print (err)
                print(traceback.format_exc())
                actor.selfLogger ('error', err)
            
