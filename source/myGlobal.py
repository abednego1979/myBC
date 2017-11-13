# -*- coding: utf-8 -*-

#Python 3.5.x


import logging
import config

logger=None
userChooseProxySet=None

class signals():
    signals={}
    
    def __init__(self):
        for marketname in config.markets:
            self.signals[marketname]={}

    def setSignal(self, market, signalName, signalValue):
        logger.debug("<setSignal><%s, %s>=%s" % (market, signalName, str(signalValue)))
        self.signals[market][signalName]=signalValue

    def getSignal(self, market, signalName):
        try:
            return self.signals[market][signalName]
        except KeyError:
            return None

sgl=signals()
