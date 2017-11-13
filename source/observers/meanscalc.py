#*- coding: utf-8 -*-
#Python 3.5.x
#utf8编码

import logging
import json
import traceback
from .observer import Observer
import myGlobal
import config

#这个Observer用于计算跟踪时间间隔的均线
class MeansCalc(Observer):
    meansLines={}
    priceLine={}

    def __init__(self):
        for marketName in config.markets:
            self.priceLine[marketName]=[]
            self.meansLines[marketName]={}
            for timeLen in config.meansLineTimeLens:
                self.meansLines[marketName][timeLen]=[]
        super(MeansCalc, self).__init__()
                
                
    def opportunity(self, tradeinfo):
        for marketName in config.markets:
            #每个市场的情况不一样
            if marketName not in tradeinfo.keys():
                #有时个别的市场数据会获取失败，这里简单跳过既可
                continue
            
            #更新每个市场的价格序列
            self.priceLine[marketName]=[{'timestamp' : tradeinfo[marketName]['timestamp'], 'price' : (tradeinfo[marketName]['info']['depth']['asks'][0]['price']+tradeinfo[marketName]['info']['depth']['bids'][0]['price'])*0.5}]+self.priceLine[marketName]
            
            #去除一些以后不再使用的价格数据
            self.priceLine[marketName] = [pricePoint for pricePoint in self.priceLine[marketName] if (self.priceLine[marketName][0]['timestamp']-pricePoint['timestamp'])<=(60*max(config.meansLineTimeLens))]
            
            for timeLen in config.meansLineTimeLens:    #minutes
                #对marketName的价格求timeLen的均线                
                tempMeanPoints = [pricePoint['price'] for pricePoint in self.priceLine[marketName] if (self.priceLine[marketName][0]['timestamp']-pricePoint['timestamp'])<=(60*timeLen)]
                self.meansLines[marketName][timeLen]=[{'timestamp' : self.priceLine[marketName][0]['timestamp'], 'price' : sum(tempMeanPoints)/len(tempMeanPoints)}]+self.meansLines[marketName][timeLen]
                    
                #self.meansLines[marketName][timeLen]['timestamp']
                #self.meansLines[marketName][timeLen]['price']
                
                #均线数据也会不断的增长，这里要去掉一些不必要的数据，就保留过去1个小时的数据吧
                self.meansLines[marketName][timeLen] = [item for item in self.meansLines[marketName][timeLen] if (self.meansLines[marketName][timeLen][0]['timestamp']-item['timestamp'])<=(60*60)]
                
                #根据当前的数据刷新信号
                tempLine=[str(item['price']) for item in self.meansLines[marketName][timeLen]]
                myGlobal.logger.debug("market:%s,meansLen:%d,Line:%s" %(marketName, timeLen, ','.join(tempLine)))
                
                pass
            pass
        

        for marketName in config.markets:
            for timeLen in config.meansLineTimeLens:    #minutes
                #检查各个均线的当前趋势和这个趋势的持续时间
                try:
                    tempDiffMean=[]
                    for i in range(len(self.meansLines[marketName][timeLen])-1):
                        tempDiffMean.append(self.meansLines[marketName][timeLen][i]['price']-self.meansLines[marketName][timeLen][i+1]['price'])
                    if not tempDiffMean:
                        tempDiffMean.append(0.0)
                        
                    if tempDiffMean[0]>=0:#最近一个点在上升
                        tempLen=0
                        for i in range(len(tempDiffMean)):
                            if tempDiffMean[i]>=0:
                                tempLen+=1
                            else:
                                break
                        
                        myGlobal.sgl.setSignal(marketName, 'meanline_'+str(timeLen)+'_trend', 'up')
                        myGlobal.sgl.setSignal(marketName, 'meanline_'+str(timeLen)+'_trend_continue', (self.meansLines[marketName][timeLen][0]['timestamp']-self.meansLines[marketName][timeLen][tempLen-1]['timestamp'])/60)
                    if tempDiffMean[0]<0:#最近一个点在下降
                        tempLen=0
                        for i in range(len(tempDiffMean)):
                            if tempDiffMean[i]<0:
                                tempLen+=1
                            else:
                                break
                        myGlobal.sgl.setSignal(marketName, 'meanline_'+str(timeLen)+'_trend', 'down')
                        myGlobal.sgl.setSignal(marketName, 'meanline_'+str(timeLen)+'_trend_continue', (self.meansLines[marketName][timeLen][0]['timestamp']-self.meansLines[marketName][timeLen][tempLen-1]['timestamp'])/60)
                except Exception as err:
                    print (err)
                    print(traceback.format_exc())                    
                    myGlobal.logger.error(err)
                pass