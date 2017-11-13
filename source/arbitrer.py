# -*- coding: utf-8 -*-
#python 3.5.x
#utf8编码

# Copyright (C) 2013, Maxime Biais <maxime@biais.org>

import public_markets
import observers
import simexchangers
import realtraders
import config
import time
import logging
import json
import traceback
from concurrent.futures import ThreadPoolExecutor, wait
from database.DB_Ex import MyDbEx
import myGlobal


class Arbitrer(object):
    def __init__(self):
        self.markets = []
        self.observers = []
        self.simexchangers = []
        self.realtraders = []
        self.depths = {}
        self.init_markets(config.markets)   #初始化市场信息，关于这些市场的信息更新时间，名称等信息
        self.init_observers(config.observers)
        self.init_simexchangers(config.simexchangers)
        self.init_realtraders(self.realtraders)
        self.threadpool = ThreadPoolExecutor(max_workers=10)        #初始化一个线程池，其他的还都没有做

    def init_markets(self, markets):
        self.market_names = markets
        for market_name in markets:
            try:
                exec('import public_markets.' + market_name.lower())
                market = eval('public_markets.' + market_name.lower() + '.' + market_name + '()')
                self.markets.append(market)
            except (ImportError, AttributeError) as e:
                print("%s market name is invalid: Ignored (you should check your config file)" % (market_name))
                
    def init_observers(self, _observers):
        self.observer_names = _observers
        for observer_name in _observers:
            try:
                exec('import observers.' + observer_name.lower())
                observer = eval('observers.' + observer_name.lower() + '.' + observer_name + '()')
                self.observers.append(observer)
            except (ImportError, AttributeError) as e:
                print("%s observer name is invalid: Ignored (you should check your config file)" % (observer_name))
                
    def init_simexchangers(self, _simexchangers):
        self.simexchanger_names = _simexchangers
        for simexchanger_name in _simexchangers:
            try:
                exec('import simexchangers.' + simexchanger_name.lower())
                simexchanger = eval('simexchangers.' + simexchanger_name.lower() + '.' + simexchanger_name + '()')
                self.simexchangers.append(simexchanger)
            except (ImportError, AttributeError) as e:
                print("%s simexchanger name is invalid: Ignored (you should check your config file)" % (simexchanger_name))
                
    def init_realtraders(self, _realtraders):
        self.realtraders_names = _realtraders
        for realtrader_name in _realtraders:
            try:
                exec('import realtraders.' + realtrader_name.lower())
                realtrader = eval('realtraders.' + realtrader_name.lower() + '.' + realtrader_name + '()')
                self.realtraders.append(realtrader)
            except (ImportError, AttributeError) as e:
                print("%s realtrader name is invalid: Ignored (you should check your config file)" % (realtrader_name))    

    def __get_market_tradeinfo(self, market, tradeinfo):
        tradeinfo[market.name] = {'info' : market.get_tradeinfo(), 'timestamp' : int(time.time())}

    def update_tradeinfo(self):
        tradeinfo = {}
        futures = []
        for market in self.markets:
            futures.append(self.threadpool.submit(self.__get_market_tradeinfo, market, tradeinfo))
        wait(futures, timeout=20)
        return tradeinfo
    
    def tickers(self):
        for market in self.markets:
            if market.name not in self.tradeinfo.keys():
                myGlobal.logger.info("Fail to get market.name information")
                continue
            tradeinfo=self.tradeinfo[market.name]
            #myGlobal.logger.info("ticker: " + market.name + " - " + str(tradeinfo))
            #记录到数据库
            #print (time.mktime(time.localtime()))
            #print (time.time())
            #print (market.symbol)
            for key in tradeinfo['info'].keys():
                #print (key)
                #print (tradeinfo['info'][key])
                pass
                
            db=MyDbEx(config.db_entry)
            for key in tradeinfo['info'].keys():
                db.DbEx_InsertItem(titleNameList=['timestamp', 'market', 'dtype', 'dvalue'], data=[tradeinfo['timestamp'], market.symbol, key, json.dumps(tradeinfo['info'][key])], needConnect=True, needCommit=True)
                pass
            pass
        pass
    
            
            
    def run_observers(self):
        for observer in self.observers:
            observer.begin_opportunity_finder()
            
        #在不同的市场中查找机会
        for observer in self.observers:
            try:
                observer.opportunity(self.tradeinfo)
            except Exception as err:
                print (err)
                print(traceback.format_exc())
                myGlobal.logger.error(err)
            pass

        for observer in self.observers:
            observer.end_opportunity_finder()
            
    def run_simexchangers(self):
        for simexchanger in self.simexchangers:
            simexchanger.begin()
            
        #在不同的市场中查找机会
        for simexchanger in self.simexchangers:
            simexchanger.simExchanger(self.tradeinfo)
            pass

        for simexchanger in self.simexchangers:
            simexchanger.end()
    
    def run_realtraders(self):
        for realtrader in self.realtraders:
            realtrader.begin()
            
        #在不同的市场中查找机会
        for realtrader in self.realtraders:
            realtrader.simExchanger(self.tradeinfo)
            pass

        for realtrader in self.realtraders:
            realtrader.end()    

    def loop(self):
        while True:
            myGlobal.logger.info("tick")
            self.tradeinfo = self.update_tradeinfo()
            self.tickers()  #这里从网络取
            self.run_observers()    #这里整理信息
            self.run_simexchangers()    #这里模拟交易
            self.run_realtraders()    #这里真实交易
            time.sleep(config.refresh_rate)
