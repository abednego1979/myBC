# -*- coding: utf-8 -*-

#Python 3.5.x

#V0.01

import traceback
import os
import copy
import re

__metaclass__ = type

#class database
class MyDB_Base():
    db_conn=None
    db_curs=None
    db_host='localhost'
    db_port=0
    db_user=''
    db_password=''
    db_name=''
    tb_name=''
    #数据库操作系列函数
    
    def __init__(self, db_entry):
        self.db_conn=None
        self.db_curs=None
        
        self.db_host=db_entry['server_ip']
        self.db_port=db_entry['port']
        self.db_user=db_entry['user']
        self.db_password=db_entry['password']
        self.db_name=db_entry['db_name']
        self.tb_name=db_entry['tb_name']
        return
    
    def CreateDB(self):
        assert 0
        pass    #由于各种数据库的创建方式不一样，所以这里是空函数，在具体的数据可实现中实例化
        
    def DropDB(self):
        assert 0
        pass
    
    def ConnectDB(self):
        assert 0
        pass
        
    def CommitDB(self):
        self.db_conn.commit()
        return
        
    def CloseDB(self):
        self.db_curs.close()
        self.db_conn.close()
        self.db_curs=None
        self.db_conn=None
        
        
    ####################################################    
    def CreateTable(self, tableConstruct, auto_increment):
        # check if the table is exist
        all_tables = self.db_curs.execute("show tables")
        tb_list=[]
        for tb in self.db_curs.fetchall():
            tb_list+=list(tb.values())
        if self.tb_name in tb_list:
            return

        # create tables
        execString="create table "+self.tb_name+" ("
        
        for index,title_type in enumerate(zip(tableConstruct['column'], tableConstruct['dataType'])):
            execString+=title_type[0]+' '+title_type[1]
            if index==0:
                if auto_increment:
                    execString+=' PRIMARY KEY NOT NULL AUTO_INCREMENT'
                else:
                    execString+=' PRIMARY KEY NOT NULL'
            execString+=','
        execString=execString.rstrip(',')
        execString+=')'
        try:
            self.db_curs.execute(execString)
        except Exception as err:
            print(('The table '+self.tb_name+' exists!'))
            print (err)
            print(traceback.format_exc())
        return
    
    def GetTable(self):
        #get all tables name
        queryString = 'SHOW TABLES'
        try:
            self.db_curs.execute(queryString)
            l_temp=[]
            for row in self.db_curs.fetchall():
                l_temp.append(copy.deepcopy(list(row.values())))
            return l_temp            
        except Exception as err:
            print('SHOW TABLES Fail')
            print (err)
            print(traceback.format_exc())       
            return []
    
    def DropTable(self):
        # drop table
        execString='drop table '+self.tb_name
        try:
            self.db_curs.execute(execString)
        except Exception as err:
            print (err)
            print(traceback.format_exc())
        return
        
    def Create_SqlCmd_SELECT(self, sql_select, sql_where, *para):
        if len(sql_where):
            str_select='SELECT '+sql_select+' FROM '+self.tb_name+' WHERE '+sql_where
        else:
            str_select='SELECT '+sql_select+' FROM '+self.tb_name
            
        for i in range(len(para)):
            s=re.search(r"(?<=')"+'##'+str(i)+r"(?=')", str_select)
            str_select=str_select.replace('##'+str(i), str(para[i]))
        return str_select
    
    def Create_SqlCmd_UPDATE(self, sql_update, sql_where, *para):
        if len(sql_where):
            str_update='UPDATE '+self.tb_name+' SET '+sql_update+' WHERE '+sql_where
        else:
            str_update='UPDATE '+self.tb_name+' SET '+sql_update
            
        for i in range(len(para)):
            s=re.search(r"(?<=')"+'##'+str(i)+r"(?=')", str_update)
            str_update=str_update.replace('##'+str(i), str(para[i]))
        return str_update
    
    def Create_SqlCmd_INSERT(self, titleNameList, data):
        insert='INSERT INTO '+self.tb_name+' SET '
        for title_value in zip(titleNameList, data):
            para1=title_value[1]
            if type(para1)==str:
                #para1='"'+para1+'"'
                para1="'"+para1.replace("'", "''")+"'"
            insert+=title_value[0]+'='+str(para1)+','
        insert=insert.rstrip(',')
        
        return insert
    

    def Query(self, query):
        #执行查询操作
        self.db_curs.execute(query)

        #取出列名称
        #names=[f[0] for f in self.db_curs.description]
        
        l_temp=[]
        for row in self.db_curs.fetchall():
            l_temp.append(list(copy.deepcopy(row)))
        return l_temp
    
    def Update(self, update):
        try:
            #执行更新操作
            self.db_curs.execute(update)
        except Exception as err:
            print ('Update Fail: ')
            print((str(update, 'utf-8')))
            print (err)
            print(traceback.format_exc())
            return -1
        return 0
    

