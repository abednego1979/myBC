#*- coding: utf-8 -*-
#Python 3.5.x
#utf8çźç 

import logging
import json
from .observer import Observer
import myGlobal


class Logger(Observer):
    def opportunity(self, tradeinfo):
        for marketName in tradeinfo.keys():
            myGlobal.logger.debug("Macket: %s, depth: %s" % (marketName, json.dumps(tradeinfo[marketName]['info']['depth'])))
