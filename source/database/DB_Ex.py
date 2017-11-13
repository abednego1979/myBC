# -*- coding: utf-8 -*-

#Python 3.5.x

#V0.01

import numpy as np
import os
import config
from .DB_MySql import MyDB_MySQL

__metaclass__ = type


#这个类将以numpy的array作为对外的数据交换方式
class MyDbEx():
    db_obj=None

    def __init__(self, db_entry):
        if config.db_type=='mysql':
            self.db_obj = MyDB_MySQL(db_entry)
        elif config.db_type=='sqlite':
            self.db_obj = MyDB_Sqlite(db_entry)
        else:
            assert 0
        return
        
    ####内部函数#########################################################

    
    ####外部函数#########################################################
    def CreateDB(self):
        self.db_obj.CreateDB()
    
    def ConnectDB(self):
        self.db_obj.ConnectDB()
        
    def CloseDB(self):
        self.db_obj.CloseDB()
    
    def CommitDB(self):
        self.db_obj.CommitDB()
    
    def CreateTable(self, tableConstruct, auto_increment):
        self.db_obj.CreateTable(tableConstruct, auto_increment)
    
    
    def DbEx_GetColumns(self):
        #查询所有的列名称

        self.db_obj.ConnectDB()
        
        query = self.db_obj.Create_SqlCmd_SELECT('*', '')
        self.db_obj.db_curs.execute(query)
        names=[f[0] for f in self.db_obj.db_curs.description]

        self.db_obj.CloseDB()
        return names

    #返回的是一个二维array，列数与入参的titleNameList长度一样
    def DbEx_GetDataByTitle(self, titleNameList, needSort=1, outDataFormat=None):    #outDataFormat: np.float64 or np.float32
        self.db_obj.ConnectDB()
        
        query=self.db_obj.Create_SqlCmd_SELECT(','.join(titleNameList), '')
        res=np.array(self.db_obj.Query(query), dtype=outDataFormat)
        
        self.db_obj.CloseDB()
        
        if needSort:
            if res.ndim==2:
                #需要排序，这里用第一列进行降序排列
                x=res.T.argsort()
                res=np.array([res[x[0].tolist()[::-1][index],:].tolist() for index in range(x.shape[1])], dtype=outDataFormat)
                
        #如果读取回来的数据是空数据，一条数据，则需要对返回的数据进行shape的调整
        if res.ndim==1:
            if res.shape[0]==0:
                #读回的是空数据
                res.shape=(0, len(titleNameList))
            else:
                #读回的只有一条数据
                res.shape=(1, len(titleNameList))
        
        return res
    
    def DbEx_InsertItem(self, titleNameList, data, needConnect=True, needCommit=True):
        if needConnect:
            self.db_obj.ConnectDB()
        
        insert = self.db_obj.Create_SqlCmd_INSERT(titleNameList, data);
        
        self.db_obj.db_curs.execute(insert)
        
        if needCommit and needConnect:
            self.db_obj.CommitDB()
        if needConnect:
            self.db_obj.CloseDB()
        return
    
    def DbEx_UpdateItem(self, titleNameList, data, needConnect=True, needCommit=True):
        if needConnect:
            self.db_obj.ConnectDB()
        
        for index,item in enumerate(titleNameList):
            if index!=0:
                #以data_array[0]为titleNameList[0]特征，修改titleNameList[index]列为data_array[index]
                para1=data[index]
                if type(para1)==str:
                    para1='"'+para1+'"'                
                para2=data[0]
                if type(para2)==str:
                    para2='"'+para2+'"'
                update=self.db_obj.Create_SqlCmd_UPDATE(titleNameList[index]+'=##0', titleNameList[0]+'=##1', para1, para2)
                self.db_obj.Update(update)
                    
                
        if needCommit:
            self.db_obj.CommitDB()
        if needConnect:
            self.db_obj.CloseDB()
        return
    

