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


#以买入后死等价格上升作为策略


class simexc_KeepWaitng_Actor():
    
    #Macket:交易市场
    #refMeanLine：参考的均线，只有在这个均线上升的区间才做交易
    #btc:要交易的byc数量
    #threshold：阈值，升值超过多少百分比就卖出
    def __init__(self, Macket, refMeanLine, btc, threshold):   #T:时间均线的时间长度，N:买卖点百分比阈值
        self.Macket=Macket
        self.refMeanLine=refMeanLine
        self.btc=btc
        self.threshold=threshold
        
        self.LoggerPrefixString="<simexcKeepWaitng:%s,%d,%f,%f>" % (Macket, refMeanLine, btc, self.threshold)
        
        #define private value
        self.curBtc=0.0   #当前btc仓位
        self.curCash=0.0   #当前资金
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
        temp=self.curCash
        return temp
    
    def getSellPrice(self, btc, depth):
        #求出卖出<btc>个币的平均价格
        tempBtc=btc
        tempBid=[]
        for bid in depth['bids']:
            if bid['amount']<tempBtc:  #供应量
                tempBid.append([bid['price'],bid['amount']])
                tempBtc-=bid['amount']
            else:
                tempBid.append([bid['price'],tempBtc])
                tempBtc=0.0
                break
        price=sum([item[0]*item[1] for item in tempBid])/btc
        self.selfLogger ('debug', "bids:%s" % (json.dumps(tempBid)))
        return price
    
    def getBuyPrice(self, btc, depth):
        tempBtc=btc
        tempBid=[]
        for ask in depth['asks']:
            if ask['amount']<tempBtc:  #供应量
                tempBid.append([ask['price'],ask['amount']])
                tempBtc-=ask['amount']
            else:
                tempBid.append([ask['price'],tempBtc])
                tempBtc=0.0
                break
        price=sum([item[0]*item[1] for item in tempBid])/btc
        self.selfLogger ('debug', "asks:%s" % (json.dumps(tempBid)))
        return price
    
    #在特定市场上以一定价格卖出一定数量的BTC
    def sellBtc(self, btc, depth):
        #先确保不会卖出太多的BTC
        assert btc<=self.curBtc
        
        
        #求出卖出<btc>个币的平均价格
        price=self.getSellPrice(btc, depth)
        
        self.selfLogger ('info', "Sell %f BTC @ %f @ %s" % (btc, price, market))
        self.selfLogger ('debug', "asks:%s" % (json.dumps(depth['asks'][:5])))
        
        self.curBtc -= btc
        self.curCash += btc*price
        pass
    #在特定市场上以一定价格买入一定数量的BTC
    def buyBtc(self, market, btc, depth):
        #求出买入<btc>个币的平均价格
        price=self.getBuyPrice(btc, depth)
        
        self.selfLogger ('info', "Buy %f BTC @ %f @ %s" % (btc, price, market))
        self.selfLogger ('debug', "bids:%s" % (json.dumps(depth['bids'][:5])))
        
        self.curBtc += btc
        self.curCash -= btc*price
        pass


    def newPriceProc(self, tradeinfo):
        #proc code for new tradeinfo
        #寻找Macket中refMeanLine均线，已经连续10分钟上升的时间点买入，在价值升值超过threshold后卖出
        
        pass


class simexc_KeepWaitng(Simexchanger):
    actors=[]
        
    def __init__(self):
        #这里初始化Actor
        self.actors=[]
        
        super(simexc_KeepWaitng, self).__init__()

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
            
