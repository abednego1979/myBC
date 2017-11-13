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


#实现的价值平衡交易模拟
#在两个市场之间，价格不会严格的同步，此生彼降或升降速度此快彼慢。但是一段时间内的趋势又是基本相同的。
#所以可以采用价值平衡交易策略。
#假设在火币和比特币中国之间，约定价值投资比例为0.40对0.60，波动阈值为1%。假定初始投资金额为10000元，
#那么一开始买入火币市场的BTC4000元，买入比特币中国的BTC6000元。如果由于双方价格波动，导致火币BTC价值占
#总价值比例超出39-41%的范围，就买入或卖出火币的BTC而买入同等价值的比特币中国的BTC，让两个市场BTC的价值重回40对60

#这种投资方案的Actor初始化参数有3个：1.市场集合，2.期望价值比例，3.价值比重波动阈值


class ValueBalance_Actor():
    
    def __init__(self, Mackets, valueRate, threshold):   #T:时间均线的时间长度，N:买卖点百分比阈值
        assert len(Mackets)==len(valueRate)==2
        
        self.Mackets=Mackets
        self.valueRate=valueRate
        self.threshold=threshold
        self.LoggerPrefixString="<ValueBalance:%s,%f>" % (json.dumps(self.Mackets), self.threshold)
        
        #状态数据
        self.curBtc={}
        for market in self.Mackets:
            self.curBtc[market]=0.0
        self.curMoney=10000.0
        
        #这个数据用于记录第一次购买的btc，也可以视为借入的btc，这样的话每次将资产以BTC计算并去掉这个初始借入的BTC，就是资产收益
        self.firstBuyBtc={}
        pass
    
    def getCurProperty(self, prices):
        temp_property=self.curMoney
        for market in self.Mackets:
            temp_property += prices[market]*self.curBtc[market]
        return temp_property
    
    #在特定市场上以一定价格卖出一定数量的BTC
    def sellBtc(self, market, btc, price):
        #先确保不会卖出太多的BTC
        btc=min(btc, self.curBtc[market])
        
        self.selfLogger ('info', "Sell %f BTC @ %f" % (btc, price))
        
        self.curBtc[market] -= btc
        self.curMoney += btc*price
        pass
    #在特定市场上以一定价格买入一定数量的BTC
    def buyBtc(self, market, btc, price):
        #先确保不会花掉太多的现金
        btc=min(btc, self.curMoney/price)
        
        self.selfLogger ('info', "Buy %f BTC @ %f" % (btc, price))
        
        self.curBtc[market] += btc
        self.curMoney -= btc*price
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
        
    def newPriceProc(self, tradeinfo):
        #先检查一下需要的信息是否齐全
        for market in self.Mackets:
            if market not in tradeinfo.keys():
                self.selfLogger ('error', "ERROR: %s, %d, %s" % (__file__, sys._getframe().f_lineno, market))
                return
        
        prices={}
        for market in self.Mackets:
            prices[market]=(tradeinfo[market]['info']['depth']['bids'][0]['price']+tradeinfo[market]['info']['depth']['asks'][0]['price'])*0.5
            
            
            
        if self.curMoney==10000.0:
            #如果现金还是初始值，那么就第一次的买入BTC
            for market in self.Mackets:
                self.buyBtc(market, self.valueRate[self.Mackets.index(market)]*self.getCurProperty(prices)/prices[market], prices[market])
                self.firstBuyBtc[market]=self.curBtc[market]
                pass
            pass
        else:
            #计算一下当前的不同市场间的BTC资产价值比例
            adjustFlag=False
            for market in self.Mackets:
                cur_rate=self.curBtc[market]*prices[market]/(self.getCurProperty(prices)-self.curMoney)
                objRate=self.valueRate[self.Mackets.index(market)]
                if not (objRate-self.threshold)<=cur_rate<=(objRate+self.threshold):
                    adjustFlag=True
                    break
            
            if adjustFlag:#判断出比例失调超过阈值，重新配重
                
                #找出BTC资产比例过高的BTC资产，卖出多余的BTC
                for market in self.Mackets:
                    #目标价值
                    objValue=self.valueRate[self.Mackets.index(market)]*self.getCurProperty(prices)
                    #当前价值
                    curValue=self.curBtc[market]*prices[market]
                    
                    if curValue-objValue>=0.1:
                        diffBtc=(curValue-objValue)/prices[market]
                        self.sellBtc(market, diffBtc, prices[market])
                
                for market in self.Mackets:
                    #目标价值
                    objValue=self.valueRate[self.Mackets.index(market)]*self.getCurProperty(prices)
                    #当前价值
                    curValue=self.curBtc[market]*prices[market]
                    
                    if objValue-curValue>=0.1:
                        diffBtc=(objValue-curValue)/prices[market]
                        self.buyBtc(market, diffBtc, prices[market])
                
            assert self.curMoney<5.0

            cur_rate={}
            trueProperty=0.0
            for market in self.Mackets:
                cur_rate[market]=self.curBtc[market]*prices[market]/(self.getCurProperty(prices)-self.curMoney)
                trueProperty += (self.curBtc[market]-self.firstBuyBtc[market])*prices[market]
            #self.selfLogger ('info', "Cur Rate: %s" % (json.dumps(cur_rate)))
            self.selfLogger ('info', "Cur Property: %f(cash:%f), True Property: %f" % (self.getCurProperty(prices), self.curMoney, trueProperty))
            pass
        pass


class simexc_ValueBalance(Simexchanger):
    actors=[]
        
    def __init__(self):
        #这里初始化Actor
        Mackets=("HUOBI_BTC_CNY", "BTCC_BTC_CNY")
        valueRate=(0.50, 0.50)
        thresholds=[0.001, 0.002, 0.003, 0.004, 0.005, 0.01]
        paraArray=[(Mackets, valueRate , threshold) for threshold in thresholds]
        self.actors=[ValueBalance_Actor(item[0], item[1], item[2]) for item in paraArray]
        super(simexc_ValueBalance, self).__init__()

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
            
