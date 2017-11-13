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


#实现利用价格波动套利交易模拟
#本模拟器为更高精度的版本，在实时价格交易中。不一定都能以bid或ask值成交，因为你的交易本身就会影响价格。
#所以交易时要考虑自己的成交量对交易价格的影响。
#另外由于一个市场和另外一个市场会存在经常性的价格差。所以两个市场间的价格差是围绕着平均价格差进行的
#
#市场买卖价格的差值补偿
#由于对一个市场来讲，买价一定比买价高，所以当价格发声波动，不能仅仅参考价格差（如[M1Buy-M2Sell]和[M1Sell-M2Buy]），还要考虑每个市场在买卖价格上的差距。
#对于每个市场，在价格不变的情况下，买入然后卖出，则损失为（BuyPrice-SellPrice），对两个市场各做一次则损失是
#[M1Buy+M2Buy-M1Sell-M2Sell]，每一轮买卖有两个阶段，所以每个阶段的平均损失是lost=[M1Buy+M2Buy-M1Sell-M2Sell]*0.5
#所以当Diff(M1BuyM2Sell)低于门限而决策买入M1卖出M2的时候，要保证低于的不光是基本门限，还要比门限还低lost
#而当Diff(M1SellM2Buy)高于门限而决策卖出M1买入M2的时候，要保证高于的不光是基本门限，还要比门限还高lost



class PriceFluctuation_Actor():
    
    def __init__(self, Mackets, BiA, Threshold):   #T:时间均线的时间长度，N:买卖点百分比阈值
        assert len(Mackets)==2
        
        self.Mackets=Mackets    #两个市场的组合
        #价格差值波动的阈值。
        #即以过去一小时价格差的数学期望为标准价格差。当前的价格差高于或低于标准价格差一定值时开始启动套利。
        self.upThreshold=Threshold
        self.downThreshold=-1*Threshold
        
        self.LoggerPrefixString="<PriceFluctuation:%s,%f,%f>" % (json.dumps(self.Mackets), BiA, Threshold)
        self.curGain={'market':Mackets, "btc":BiA, "Th":Threshold, "ts":0, "curGain":0.0, "GainLastHour":0.0, "buyNum":0, "sellNum":0}
        
        #借来的btc数量
        self.BASEBTC=BiA
        self.borrowedBtcs={}
        for market in self.Mackets:
            self.borrowedBtcs[market]=self.BASEBTC
        
        #当前状态
        self.pastPricesDiff_M1BuyM2Sell=[]      #M1BuyPrice-M2SellPrice的曲线
        self.pastPricesDiff_M1SellM2Buy=[]      #M1SellPrice-M2BuyPrice的曲线
        self.pastMeanPriceDiff_M1BuyM2Sell=0.0  #M1BuyPrice-M2SellPrice曲线的近期均值
        self.pastMeanPriceDiff_M1SellM2Buy=0.0  #M1SellPrice-M2BuyPrice曲线的近期均值
        self.singleLost=[]                      #单笔交易损失历史曲线，[M1Buy+M2Buy-M1Sell-M2Sell]*0.5
        self.singleLostMean=0.0                 #单笔交易损失历史曲线的近期均值
        
        self.curBtc=self.borrowedBtcs.copy()   #当前手中的BTC数量
        self.curCash={}  #当前手中的现金数量
        for market in self.Mackets:
            self.curCash[market]=0.0
        pass
    
    def getCurProperty(self):
        return self.curCash[self.Mackets[0]]+self.curCash[self.Mackets[1]]
    
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
    def sellBtc(self, market, btc, depth):
        #先确保不会卖出太多的BTC
        assert btc<=self.curBtc[market]        
        
        
        #求出卖出<btc>个币的平均价格
        price=self.getSellPrice(btc, depth)
        
        self.selfLogger ('info', "Sell %f BTC @ %f @ %s" % (btc, price, market))
        self.selfLogger ('debug', "asks:%s" % (json.dumps(depth['asks'][:5])))
        
        self.curBtc[market] -= btc
        self.curCash[market] += btc*price
        
        self.curGain['sellNum']+=btc # 记录一下进行过多少btc的交易
        pass
    #在特定市场上以一定价格买入一定数量的BTC
    def buyBtc(self, market, btc, depth):
        #求出买入<btc>个币的平均价格
        price=self.getBuyPrice(btc, depth)
        
        self.selfLogger ('info', "Buy %f BTC @ %f @ %s" % (btc, price, market))
        self.selfLogger ('debug', "bids:%s" % (json.dumps(depth['bids'][:5])))
        
        self.curBtc[market] += btc
        self.curCash[market] -= btc*price
        
        self.curGain['buyNum']+=btc # 记录一下进行过多少btc的交易
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
            
        #获取各个市场的买卖一定量btc的价格
        prices={}
        for market in self.Mackets:
            prices[market]={'sellprice':self.getSellPrice(self.BASEBTC, tradeinfo[market]['info']['depth']), 'buyprice':self.getBuyPrice(self.BASEBTC, tradeinfo[market]['info']['depth'])}
        self.selfLogger ('info', "prices:%s" % (json.dumps(prices)))
        
        
        meanSecondsLen=600      #600s
            
        #记录最新信息的时间戳和价格差，这里有两个差价，因为交易的时候一定是一个市场买，另一个市场卖，所以差价曲线
        #一个是Market0买入价 减去 Market1卖出价
        #一个是Market0卖出价 减去 Market1买入价
        self.pastPricesDiff_M1BuyM2Sell=[(tradeinfo[self.Mackets[0]]['timestamp'], prices[self.Mackets[0]]['buyprice']-prices[self.Mackets[1]]['sellprice'])]+self.pastPricesDiff_M1BuyM2Sell
        self.pastPricesDiff_M1SellM2Buy=[(tradeinfo[self.Mackets[0]]['timestamp'], prices[self.Mackets[0]]['sellprice']-prices[self.Mackets[1]]['buyprice'])]+self.pastPricesDiff_M1SellM2Buy
    
        #只保留最近一个小时的数据
        self.pastPricesDiff_M1BuyM2Sell = [item for item in self.pastPricesDiff_M1BuyM2Sell if (self.pastPricesDiff_M1BuyM2Sell[0][0]-item[0])<=meanSecondsLen]
        self.pastPricesDiff_M1SellM2Buy = [item for item in self.pastPricesDiff_M1SellM2Buy if (self.pastPricesDiff_M1SellM2Buy[0][0]-item[0])<=meanSecondsLen]
        #求出过去一个小时内的价格均值
        tempPrice=[item[1] for item in self.pastPricesDiff_M1BuyM2Sell]
        self.pastMeanPriceDiff_M1BuyM2Sell=sum(tempPrice)/len(tempPrice)
        tempPrice=[item[1] for item in self.pastPricesDiff_M1SellM2Buy]
        self.pastMeanPriceDiff_M1SellM2Buy=sum(tempPrice)/len(tempPrice)
        
        #记录单笔交易损失[M1Buy+M2Buy-M1Sell-M2Sell]*0.5
        self.singleLost=[(tradeinfo[self.Mackets[0]]['timestamp'], (prices[self.Mackets[0]]['buyprice']+prices[self.Mackets[1]]['buyprice']-prices[self.Mackets[0]]['sellprice']-prices[self.Mackets[1]]['sellprice'])*0.5)]+self.singleLost
        #只保留最近一个小时的数据
        self.singleLost = [item for item in self.singleLost if (self.singleLost[0][0]-item[0])<=meanSecondsLen]
        #求出过去一个小时内的价格均值
        tempPrice=[item[1] for item in self.singleLost]
        self.singleLostMean=sum(tempPrice)/len(tempPrice)
        
        if (self.pastPricesDiff_M1BuyM2Sell[0][0]-self.pastPricesDiff_M1BuyM2Sell[-1][0])<(3*60):
            #如果获取的数据还不足10分钟，就不要开始交易
            return
        
        assert self.curBtc[self.Mackets[0]]+self.curBtc[self.Mackets[1]]==(2*self.BASEBTC)
        assert self.curBtc[self.Mackets[0]]==0 or self.curBtc[self.Mackets[0]]==self.BASEBTC or self.curBtc[self.Mackets[0]]==(2*self.BASEBTC)
        assert self.curBtc[self.Mackets[1]]==0 or self.curBtc[self.Mackets[1]]==self.BASEBTC or self.curBtc[self.Mackets[1]]==(2*self.BASEBTC)
        
        #当前价格差偏移，如果值大于0则第一个市场目前btc价格偏高，否则第二个市场目前btc价格偏高
        curPriceDiffBias_M1BuyM2Sell=self.pastPricesDiff_M1BuyM2Sell[0][1]-self.pastMeanPriceDiff_M1BuyM2Sell
        curPriceDiffBias_M1SellM2Buy=self.pastPricesDiff_M1SellM2Buy[0][1]-self.pastMeanPriceDiff_M1SellM2Buy
    
        self.selfLogger ('debug', "当前两市场价差_M1BuyM2Sell:%f" % (self.pastPricesDiff_M1BuyM2Sell[0][1]))
        self.selfLogger ('debug', "当前两市场价差_M1SellM2Buy:%f" % (self.pastPricesDiff_M1SellM2Buy[0][1]))
    
        self.selfLogger ('debug', "两市场价差均值_M1BuyM2Sell:%f" % (self.pastMeanPriceDiff_M1BuyM2Sell))
        self.selfLogger ('debug', "两市场价差均值_M1SellM2Buy:%f" % (self.pastMeanPriceDiff_M1SellM2Buy))
        
        self.selfLogger ('debug', "单次交易损失均值:%f" % (self.singleLostMean))
    
        self.selfLogger ('debug', "价差偏离_M1BuyM2Sell:%f(Th=%f)" % (curPriceDiffBias_M1BuyM2Sell, self.downThreshold-self.singleLostMean))
        self.selfLogger ('debug', "价差偏离_M1SellM2Buy:%f(Th=%f)" % (curPriceDiffBias_M1SellM2Buy, self.upThreshold+self.singleLostMean))
        
        #开始主处理
        if self.curBtc[self.Mackets[0]]==self.BASEBTC:
            #目前是平衡态
            assert self.curBtc[self.Mackets[1]]==self.BASEBTC
            if curPriceDiffBias_M1BuyM2Sell<=(self.downThreshold-self.singleLostMean):#如果“M1买M2卖”价格差价低于门限下限，说明可以M1买入M2卖出了
                self.buyBtc(self.Mackets[0], self.BASEBTC, tradeinfo[self.Mackets[0]]['info']['depth'])
                self.sellBtc(self.Mackets[1], self.BASEBTC, tradeinfo[self.Mackets[1]]['info']['depth'])
            elif curPriceDiffBias_M1SellM2Buy>=(self.upThreshold+self.singleLostMean):#如果“M1卖M2买”价格差价高于门限上限，说明可以M1卖出M2买入了
                self.sellBtc(self.Mackets[0], self.BASEBTC, tradeinfo[self.Mackets[0]]['info']['depth'])
                self.buyBtc(self.Mackets[1], self.BASEBTC, tradeinfo[self.Mackets[1]]['info']['depth'])
            else:
                #do nothing
                pass                
        elif self.curBtc[self.Mackets[0]]==0:
            #目前处于M1已经卖出，M2已经买入的状态
            assert self.curBtc[self.Mackets[1]]==(2*self.BASEBTC)
            if curPriceDiffBias_M1BuyM2Sell<(self.downThreshold-self.singleLostMean):
                self.buyBtc(self.Mackets[0], self.BASEBTC, tradeinfo[self.Mackets[0]]['info']['depth'])
                self.sellBtc(self.Mackets[1], self.BASEBTC, tradeinfo[self.Mackets[1]]['info']['depth'])
                #恢复到平衡态
                self.recordGain(curTimestamp, self.getCurProperty(), 0.0)
                self.buyBtc(self.Mackets[0], self.BASEBTC, tradeinfo[self.Mackets[0]]['info']['depth'])
                self.sellBtc(self.Mackets[1], self.BASEBTC, tradeinfo[self.Mackets[1]]['info']['depth'])                
            else:
                #do nothing
                pass
        elif self.curBtc[self.Mackets[0]]==(2*self.BASEBTC):
            #目前处于M1已经买入，M2已经卖出的状态
            assert self.curBtc[self.Mackets[1]]==0
            if curPriceDiffBias_M1SellM2Buy>=(self.upThreshold+self.singleLostMean):
                self.sellBtc(self.Mackets[0], self.BASEBTC, tradeinfo[self.Mackets[0]]['info']['depth'])
                self.buyBtc(self.Mackets[1], self.BASEBTC, tradeinfo[self.Mackets[1]]['info']['depth'])
                #恢复到平衡态
                self.recordGain(curTimestamp, self.getCurProperty(), 0.0)
                self.sellBtc(self.Mackets[0], self.BASEBTC, tradeinfo[self.Mackets[0]]['info']['depth'])
                self.buyBtc(self.Mackets[1], self.BASEBTC, tradeinfo[self.Mackets[1]]['info']['depth'])
            else:
                #do nothing
                pass
        else:
            assert 0

        if self.curBtc[self.Mackets[0]]==self.BASEBTC:
            assert self.curBtc[self.Mackets[1]]==self.BASEBTC
            self.recordGain(curTimestamp, self.getCurProperty(), 0.0)
        pass
    
    def recordGain(self, timestamp, curGain, GainLastHour):
        self.curGain['ts']=timestamp
        self.curGain['curGain']=curGain
        self.curGain['GainLastHour']=GainLastHour
        self.selfLogger ('info', "CurProperty:%f" % (curGain))


class simexc_PriceFluctuation(Simexchanger):
    actors=[]
        
    def __init__(self):
        #这里初始化Actor
        self.Mackets=("HUOBI_BTC_CNY", "BTCC_BTC_CNY")
        btcBiAs=[0.3, 0.5, 0.7, 1.0, 1.2, 1.5]#borrowing in advance
        thresholds=[20, 40, 50, 60, 80, 100] #yuan
        paraArray=[(self.Mackets, BiA, threshold) for BiA in btcBiAs for threshold in thresholds]
        self.actors=[PriceFluctuation_Actor(item[0], item[1], item[2]) for item in paraArray]

        super(simexc_PriceFluctuation, self).__init__()

    #准备工作
    def begin(self):
        pass

    #收尾工作
    def end(self):
        tempGain=[actor.curGain for actor in self.actors]
        tempGain.sort(key=lambda x:x['curGain'])
        for item in tempGain:
            myGlobal.logger.info ("curGainSort:%s" % (json.dumps(item)))
        pass
    
    def simExchanger(self, tradeinfo):
        for actor in self.actors:
            try:
                actor.newPriceProc(tradeinfo)
            except Exception as err:
                print (err)
                print(traceback.format_exc())
                actor.selfLogger ('error', err)
            
