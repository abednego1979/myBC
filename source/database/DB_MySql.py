# -*- coding: utf-8 -*-

#Python 3.5.x

#V0.01

import traceback
import datetime
import os
import copy
import re

import pymysql.cursors
from .DB_Base import MyDB_Base

__metaclass__ = type

#class database
class MyDB_MySQL(MyDB_Base):
    #重载的函数
    
    def __init__(self, db_entry):
        super().__init__(db_entry)
        
    def CreateDB(self):
        config = {'host':self.db_host,\
                  'port':self.db_port,\
                  'user':self.db_user,\
                  'password':self.db_password,\
                  'charset':'utf8mb4',\
                  'cursorclass':pymysql.cursors.DictCursor}
        # Connect to the database
        conn = pymysql.connect(**config)        
        curs = conn.cursor()
        
        # check if the db is exist
        db_list=[]
        curs.execute('show databases')
        for db in curs.fetchall():
            db_list.append(db['Database'])
        
        if self.db_name in db_list:
            return
        
        # create a database
        try:
            curs.execute('create database '+self.db_name)
        except:
            print('Database '+self.db_name+' exists!')
            
        conn.select_db(self.db_name)   
                
        conn.commit()
        curs.close()
        conn.close()       
        return
    
    def DropDB(self):
        config = {'host':self.db_host,\
                  'port':self.db_port,\
                  'user':self.db_user,\
                  'password':self.db_password,\
                  'charset':'utf8mb4',\
                  'cursorclass':pymysql.cursors.DictCursor}
        # Connect to the database
        conn = pymysql.connect(**config)        
        curs = conn.cursor()
        
        # drop the database
        try:
            curs.execute('drop database if exists '+self.db_name)
        except:
            print('Drop Database '+self.db_name+' Fail!')
            
        conn.commit()
        curs.close()
        conn.close()         
        return
        
        
    def ConnectDB(self):
        config = {'host':self.db_host,\
                  'port':self.db_port,\
                  'user':self.db_user,\
                  'password':self.db_password,\
                  'db':self.db_name,\
                  'charset':'utf8mb4',\
                  'cursorclass':pymysql.cursors.DictCursor}
        
        # Connect to the database
        self.db_conn = pymysql.connect(**config)
        self.db_curs = self.db_conn.cursor()
        return
        
     
