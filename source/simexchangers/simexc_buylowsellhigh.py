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


#实现低买高卖策略的模拟
#每个交易者有一个虚拟交易量。并且有一个标记持仓状态的标记"Empty"/"Full"，初始的状态是"Empty"。
#在"Empty"状态下，模拟器会不断检查价格，并记录下自从变为"Empty"状态以来的最低价格。
#当当前价格高于近期最低价格n%的时候，就买入。并且将状态设置为"Full"
#在"Full"状态下，模拟器会不断检查价格，并记录下自从变为"Full"状态以来的最高价格。
#当当前价格低于近期最高价格n%的时候，就买入。并且将状态设置为"Empty"

#而参考价格可以采用3分钟，5分钟，10分钟，30分钟，60分钟，1天等时间长度均线。
#而确定交易点的n值也可以采用1，3，5，8，10，20等。

#实现的时候对不同的价格均线和n值创建多线程。以期找到某一段时间的最佳交易策略

class BLSH_Actor():
    
    def __init__(self, Macket, T, N):   #T:时间均线的时间长度，N:买卖点百分比阈值
        self.Macket=Macket
        self.T=T
        self.N=N
        self.priceCurve=[]
        self.lastPrice=None
        self.LoggerPrefixString="<BuyLowSellHigh:%d,%f>" % (self.T, self.N)
        
        self.position='Empty'#仓位,Full or Empty
        self.nearLowPrice=0.0
        self.nearHighPrice=0.0
        self.curBtc=0.0
        self.curMoney=10000.0
    
    def getCurProperty(self, price):
        return self.curMoney+price*self.curBtc
    
    
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
        
    def newPriceProc(self, tradeinfo):
        if self.Macket not in tradeinfo.keys():
            return
        
        newPrice = {'timestamp' : tradeinfo[self.Macket]['timestamp'], 'bid' : tradeinfo[self.Macket]['info']['depth']['bids'][0]['price'], 'ask' : tradeinfo[self.Macket]['info']['depth']['asks'][0]['price']}
        
        #针对本actor使用的时间均线的时间长度参数，作出均线
        #然后基于以上数据进行决策
        self.selfLogger ('info', "Macket : %s, T : %d minutes, N : %f" % (self.Macket, self.T, self.N))
        self.selfLogger ('debug', "newPrice: bid : %f, ask : %f, (bid+ask)*0.5 : %f" % (newPrice['bid'], newPrice['ask'], (newPrice['bid']+newPrice['ask'])*0.5))

        #先将最新价格增加到价格曲线
        self.priceCurve=[newPrice]+self.priceCurve
    
        if self.T:
            tempPriceCurve=[item for item in self.priceCurve if (newPrice['timestamp']-item['timestamp'])<int(self.T * 60)]
        else:#self.T==0时代表用实时数据进行交易，这时计算的均值只使用当前的一个数据
            tempPriceCurve=[self.priceCurve[0]]
        #舍弃一些无用的数据。只保留用于计算均线的数据
        self.priceCurve=self.priceCurve[:len(tempPriceCurve)]
        
        tempPriceBid=[item['bid'] for item in tempPriceCurve]
        bidMean=sum(tempPriceBid)/len(tempPriceBid)
        tempPriceAsk=[item['ask'] for item in tempPriceCurve]
        askMean=sum(tempPriceAsk)/len(tempPriceAsk)
        
        self.lastPrice={'timestamp' : newPrice['timestamp'], 'price' : (bidMean+askMean)/2.0}
        
        #下面依据当前价格，空满仓状态，以及均值曲线确定买卖点
        #注意使用的当前价格应是当前绝对价格还是一个均值价格？        
        curRealPrice=(newPrice['bid']+newPrice['ask'])/2.0
        curMeanPrice=self.lastPrice['price']
        
        curTargetPrice=curMeanPrice #指标价格，用这个价格去和近期最低价和近期最高价比较
        if self.position=='Empty':
            #求最近的均线最低价格
            if not self.nearLowPrice:
                self.nearLowPrice=self.lastPrice['price']
            else:
                if self.lastPrice['price']<self.nearLowPrice:
                    self.nearLowPrice=self.lastPrice['price']
            self.selfLogger ('info', "Cur/Low:%f/%f=%f" % (curMeanPrice, self.nearLowPrice, curMeanPrice/self.nearLowPrice))
            self.selfLogger ('debug', "lastPrice:%f" % (self.lastPrice['price']))

            #如果当前价格超过之前最低价的N%,就买入
            thresholdMeanTime=60#
            if myGlobal.sgl.getSignal(self.Macket, 'meanline_'+str(thresholdMeanTime)+'_trend') == 'up' and myGlobal.sgl.getSignal(self.Macket, 'meanline_'+str(thresholdMeanTime)+'_trend_continue') > 3:
                #上面这个条件是要求在60分钟均线在上升阶段才买入
                if curMeanPrice > self.nearLowPrice*(1+self.N):
                    #买入
                    self.curBtc += self.curMoney/curRealPrice
                    self.curMoney = 0.0
                    self.selfLogger ('info', "Transaction:Buy:price:%f, curProperty:%f" % (curRealPrice, self.getCurProperty(curRealPrice)))
                    
                    self.nearHighPrice=self.lastPrice['price']
                    self.position='Full'
        elif self.position=='Full':
            #求最近的均线最高价格
            if not self.nearHighPrice:
                self.nearHighPrice=self.lastPrice['price']
            else:
                if self.lastPrice['price']>self.nearHighPrice:
                    self.nearHighPrice=self.lastPrice['price']
            self.selfLogger ('info', "Cur/High:%f/%f=%f" % (curMeanPrice, self.nearHighPrice, curMeanPrice/self.nearHighPrice))
            self.selfLogger ('debug', "lastPrice:%f" % (self.lastPrice['price']))
            #如果当前价格低于之前最高价的N%,就卖出
            if curMeanPrice < self.nearHighPrice*(1-self.N*0.5):#割肉要快
                #卖出
                self.curMoney += self.curBtc*curRealPrice
                self.curBtc = 0.0
                
                self.selfLogger ('info', "Transaction:Sell:price:%f, curProperty:%f" % (curRealPrice, self.getCurProperty(curRealPrice)))
                
                self.nearLowPrice=self.lastPrice['price']
                self.position='Empty'
        else:
            assert 0
        
        pass


class simexc_BuyLowSellHigh(Simexchanger):
    actors=[]
        
    def __init__(self):
        nArray=[0.001, 0.005, 0.01, 0.03, 0.05, 0.08, 0.10, 0.20]
        paraArray=[(x,y,z) for x in config.markets for y in config.meansLineTimeLens for z in nArray]
        self.actors=[BLSH_Actor(item[0], item[1], item[2]) for item in paraArray]
        super(simexc_BuyLowSellHigh, self).__init__()

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
            
