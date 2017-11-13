# -*- coding: utf-8 -*-
#Python 3.5.x
#utf8编码

markets = [
"HUOBI_BTC_CNY",
"BTCC_BTC_CNY",
]

# observers if any
# ["Logger", "TraderBotSim", "Emailer"]
observers = ["Logger", "DbRecorder", "MeansCalc"]


#模拟的交易策略
#simexcBuyLowSellHigh：低买高卖，价格均线涨幅超过一定水平就买入，价格均线跌幅超过一定水平就卖出
#simexcLadderPrice：阶梯价格，即在某均线下降和上升中按不同阶梯价格买入和卖出
#simexcValueBalance：价值均衡，即重视尽量保持两个市场的btc资产比例一定
#simexcPriceFluctuation：套利交易
#其他可以考虑均线走势，买卖力量对比，苦等升值N%, 多市场平衡等
simexchangers = [
'simexc_Template',
#'simexc_BuyLowSellHigh', 
#'simexc_ValueBalance',
'simexc_PriceFluctuation',
]

realtraders = [
'realtrade_Template',
]

meansLineTimeLens = [0,1,3,5,10,30,60]

# [db_info]
db_type = 'mysql'
# [db_entry_mysql]
db_entry = {'server_ip': 'localhost', \
            'port': 3306, \
            'user': 'zhy', \
            'password': '123456', \
            'db_name': 'btc_db', \
            'tb_name': 'vc_data'}

#proxy相关
config_proxy_en='on'
#How to create enctrypt message:
#from Crypto.Cipher import AES
#obj = AES.new('MY KEY!!!!', AES.MODE_CBC, b'0000000000000000')    len of 'MY KEY!!!!' must be 16, 24, or 32 bytes long
#message = json.dumps(<<<<dict or other python object>>>>)+'MAGIC'
#message+='' if not len(message)%16 else ' '*(16-len(message)%16)
#ciphertext = obj.encrypt(message)
#print (str(base64.b64encode(ciphertext), encoding = "utf-8"))          the input is the encrypted information
config_proxy_info = "+xIGTSdXLxw2mdsilaRypGf6hutl2ucuBdiIYKTedm+Hagojd3bOMzPqLqutDo/1vZnTUy4FIOYrTJ8NkLlvrZjVSW0rm4ptBakiL2EFufYvGVOoIlQlKQZVWTDYo61SsUvUITPMurgHW3+MgkagCOJTYnSJl/KvaJEnrmSC+X7mtThFRwDIDoZzuZDTTfH9"


#logger日志相关
logger_console='on'
logger_console_level='INFO'
logger_file='on'
logger_file_level='DEBUG'



market_expiration_time = 120  # in seconds: 2 minutes

refresh_rate = 20

#### Trader Bot Config
# Access to Private APIs

paymium_username = "FIXME"
paymium_password = "FIXME"
paymium_address = "FIXME"  # to deposit btc from markets / wallets

bitstamp_username = "FIXME"
bitstamp_password = "FIXME"

# SafeGuards
max_tx_volume = 10  # in BTC
min_tx_volume = 1  # in BTC
balance_margin = 0.05  # 5%
profit_thresh = 1  # in EUR
perc_thresh = 2  # in %

#### Emailer Observer Config
smtp_host = 'FIXME'
smtp_login = 'FIXME'
smtp_passwd = 'FIXME'
smtp_from = 'FIXME'
smtp_to = 'FIXME'

#### XMPP Observer
xmpp_jid = "FROM@jabber.org"
xmpp_password = "FIXME"
xmpp_to = "TO@jabber.org"
