#*- coding: utf-8 -*-
#Python 3.5.x
#utf8编码

import config
from .observer import Observer
from database.DB_Ex import MyDbEx


class DbRecorder(Observer):
    db=None
    
    #某些准备工作
    def begin_opportunity_finder(self):
        if not self.db:
            self.db=MyDbEx(config.db_entry)
        pass

    #opportunity_finder的收尾工作
    def end_opportunity_finder(self):
        pass
    
    def opportunity(self, tradeinfo):
        pass
