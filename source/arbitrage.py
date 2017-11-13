# -*- coding: utf-8 -*-
#Python 3.5.x
#utf8编码

# Copyright (C) 2013, Maxime Biais <maxime@biais.org>

import logging
import logging.handlers
import argparse
import sys
import public_markets
import database
import glob
import os
import traceback
import inspect
from arbitrer import Arbitrer
import config
import time
import re

import configparser

import myGlobal
from database.DB_Ex import MyDbEx

class ArbitrerCLI:
    def __init__(self):
        pass


    def exec_command(self, args):
        if "watch" in args.command:
            self.create_arbitrer(args)
            self.arbitrer.loop()
        if "list-public-markets" in args.command:
            self.list_markets()

    def list_markets(self):
        for filename in glob.glob(os.path.join(public_markets.__path__[0], "*.py")):
            module_name = os.path.basename(filename).replace('.py', '')
            if not module_name.startswith('_'):
                module = __import__("public_markets." + module_name)
                test = eval('module.' + module_name)
                for name, obj in inspect.getmembers(test):
                    if inspect.isclass(obj) and 'Market' in (j.__name__ for j in obj.mro()[1:]):
                        if not obj.__module__.split('.')[-1].startswith('_'):
                            print(obj.__name__)
        sys.exit(0)

    def create_arbitrer(self, args):
        self.arbitrer = Arbitrer()
        if args.observers:
            self.arbitrer.init_observers(args.observers.split(","))        
        if args.markets:
            self.arbitrer.init_markets(args.markets.split(","))

    def init_logger(self, args):        
        # 定义日志输出格式
        formatString='%(asctime)s [%(levelname)s] %(message)s'
        
        # 初始化
        logging.basicConfig()
        
        #创建日志对象并设置级别
        myGlobal.logger = logging.getLogger('baselogger')
        myGlobal.logger.setLevel(logging.DEBUG)
        myGlobal.logger.propagate = False
        
        if config.logger_console=='on':
            #######################################
            #创建一个日志输出处理对象
            hdr = logging.StreamHandler()
            hdr.setLevel(config.logger_console_level)
            hdr.setFormatter(logging.Formatter(formatString))
            #######################################
            myGlobal.logger.addHandler(hdr)
        
        if config.logger_file=='on':
            #######################################
            #创建一个日志文件输出处理对象
            fileshandle = logging.handlers.TimedRotatingFileHandler('procLog_', when='H', interval=2, backupCount=0)
            # 设置日志文件后缀，以当前时间作为日志文件后缀名。
            fileshandle.suffix = "%Y%m%d_%H%M%S.log"
            fileshandle.extMatch = re.compile(r"^\d{4}\d{2}\d{2}_\d{2}\d{2}\d{2}.log$")
            # 设置日志输出级别和格式
            fileshandle.setLevel(config.logger_file_level)
            fileshandle.setFormatter(logging.Formatter(formatString))
            #######################################
            myGlobal.logger.addHandler(fileshandle)

        pass
    

    def main(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("-o", "--observers", type=str,
                            help="observers, example: -oLogger,Emailer")
        parser.add_argument("-m", "--markets", type=str,
                            help="markets, example: -mMtGox,Bitstamp")
        parser.add_argument("command", nargs='*', default="watch",
                            help='verb: "watch|replay-history|get-balance|list-public-markets"')
        args = parser.parse_args()
        self.init_logger(args)
        self.exec_command(args)
        
        

def main():

    #检查是否存在mysql数据库，如果不存在就创建一个
    #数据库的基本数据格式有时间戳（id），marcket（同一个交易所的不同币种认为是不同市场），datatype（深度，交易等），data（json格式）
    try:
        if 'mysql'==config.db_type:
            print ('use MySQL Database.')
        elif 'sqlite'==config.db_type:
            print ('use Sqlite Database.')
        else:
            assert 0
            
        db=MyDbEx(config.db_entry)
        db.CreateDB()
        print ('Create a New DataBase')
        db.ConnectDB()
        db.CreateTable({'column': ['id', 'timestamp', 'market', 'dtype', 'dvalue'], 'dataType': ['int', 'BIGINT UNSIGNED', 'CHAR(16)', 'CHAR(16)', 'TEXT']}, True)
        db.CommitDB()
        db.CloseDB()
    except Exception as err:
        print (err)
        print(traceback.format_exc())
        return
    
    myGlobal.userChooseProxySet=config.config_proxy_en
    if config.config_proxy_en=='on':
        proxyChoose=input('The PROXY is on, Right?(Y/N)')
        if proxyChoose=='N' or proxyChoose=='n':
            myGlobal.userChooseProxySet='off'
    
    cli = ArbitrerCLI()
    cli.main()

if __name__ == "__main__":
    main()
