# encoding: UTF-8

from __future__ import absolute_import
from builtins import str
from builtins import range
from builtins import object

import time
import json
import traceback

from vtGateway import *
from jaqs.trade.tradeapi import TradeApi
from jaqs.data import DataApi
from .quantosLoginWidget import QuantOSLoginEngine


def check_return_error(res, err_msg):
    if res is None:
        return False
    else:
        return True
        
# functions for generating algo parameters

#----------------------------------------------------------------------
def generateEmptyParams(security, urgency):
    """generate empty dict"""
    return {}

#----------------------------------------------------------------------
def generateVwapParams(security, urgency):
    """generate params for vwap algo"""
    params = {}
    params['urgency'] = {security: urgency}               # bid + 0.25 * bid_ask_spread
    params['participate_rate'] = {security: 0.1}
    params['price_range_factor'] = 0.1
    params['lifetime'] = 600000                     # 10 minutes     
    return params

#----------------------------------------------------------------------
def generateTwapParams(security, urgency):
    """generate params for twap algo"""
    params = {}
    params['urgency'] = {security: urgency}               # bid + 0.25 * bid_ask_spread
    params['price_range_factor'] = 0.1
    params['cycle'] = 1000
    params['lifetime'] = 60000                     # 10 minutes     
    return params

# 以下为一些VT类型和quantos类型的映射字典
# 价格类型映射
priceTypeMap = {}
priceTypeMap[PRICETYPE_LIMITPRICE] = ('', generateEmptyParams)
priceTypeMap[PRICETYPE_VWAP] = ('vwap', generateVwapParams)
priceTypeMap[PRICETYPE_TWAP] = ('twap', generateTwapParams)

# 动作印射
actionMap = {}
actionMap[(DIRECTION_LONG, OFFSET_OPEN)] = "Buy"
actionMap[(DIRECTION_SHORT, OFFSET_OPEN)] = "Short"
actionMap[(DIRECTION_LONG, OFFSET_CLOSE)] = "Cover"
actionMap[(DIRECTION_SHORT, OFFSET_CLOSE)] = "Sell"
actionMap[(DIRECTION_LONG, OFFSET_CLOSEYESTERDAY)] = "CoverYesterday"
actionMap[(DIRECTION_SHORT, OFFSET_CLOSEYESTERDAY)] = "SellYesterday"
actionMap[(DIRECTION_LONG, OFFSET_CLOSETODAY)] = "CoverToday"
actionMap[(DIRECTION_SHORT, OFFSET_CLOSETODAY)] = "SellToday"
actionMap[(DIRECTION_LONG, OFFSET_UNKNOWN)] = "AutoLong"
actionMap[(DIRECTION_SHORT, OFFSET_UNKNOWN)] = "AutoShort"
actionMapReverse = {v: k for k, v in list(actionMap.items())}

# 交易所类型映射
exchangeMap = {}
exchangeMap[EXCHANGE_CFFEX] = 'CFE'
exchangeMap[EXCHANGE_SHFE] = 'SHF'
exchangeMap[EXCHANGE_CZCE] = 'CZC'
exchangeMap[EXCHANGE_DCE] = 'DCE'
exchangeMap[EXCHANGE_SSE] = 'SH'
exchangeMap[EXCHANGE_SZSE] = 'SZ'
exchangeMap[EXCHANGE_SGE] = 'SGE'
exchangeMap[EXCHANGE_CSI] = 'CSI'
exchangeMap[EXCHANGE_HKS] = 'HKS'
exchangeMap[EXCHANGE_HKH] = 'HKH'
exchangeMap[EXCHANGE_JZ] = 'JZ'
exchangeMap[EXCHANGE_SPOT] = 'SPOT'
exchangeMap[EXCHANGE_IB] = 'IB'
exchangeMap[EXCHANGE_FX] = 'FX'
exchangeMap[EXCHANGE_INE] = 'INE'

exchangeMapReverse = {v:k for k,v in list(exchangeMap.items())}

# 持仓类型映射
sideMap = {}
sideMap[DIRECTION_LONG] = 'Long'
sideMap[DIRECTION_SHORT] = 'Short'
sideMapReverse = {v:k for k,v in list(sideMap.items())}

# 产品类型映射
productClassMapReverse = {}
productClassMapReverse[1] = PRODUCT_EQUITY
productClassMapReverse[3] = PRODUCT_EQUITY
productClassMapReverse[4] = PRODUCT_EQUITY
productClassMapReverse[5] = PRODUCT_EQUITY
productClassMapReverse[8] = PRODUCT_BOND
productClassMapReverse[17] = PRODUCT_BOND
productClassMapReverse[101] = PRODUCT_FUTURES
productClassMapReverse[102] = PRODUCT_FUTURES
productClassMapReverse[103] = PRODUCT_FUTURES

# 委托状态映射
statusMapReverse = {}
statusMapReverse['New'] = STATUS_UNKNOWN
statusMapReverse['Accepted'] = STATUS_NOTTRADED
statusMapReverse['Cancelled'] = STATUS_CANCELLED
statusMapReverse['Filled'] = STATUS_ALLTRADED
statusMapReverse['Rejected'] = STATUS_REJECTED



########################################################################
class QuantOSGateway(VtGateway):
    #----------------------------------------------------------------------
    def __init__(self, eventengine, dataengine, gatewayName='quantos'):
        """Constructor"""
        super(QuantOSGateway, self).__init__(eventengine, gatewayName)
        
        f = open("setting/VT_setting.json", "r")
        setting = json.load(f)
        
        self.mdApi = QuantOSMdApi(self, setting)      # 行情
        self.tdApi = QuantOSTdApi(self, setting)      # 交易
        
        self.qryEnabled = False         # 是否要启动循环查询
        self.loginWindow = QuantOSLoginEngine(self, setting)
        
        self.dataengine = dataengine
        
    def connect(self):
        self.loginWindow.show()
        
    def getStrategyList(self, userName, password):
        return self.tdApi.getStrategyList(userName, password)
    
    #----------------------------------------------------------------------
    def login(self, username, token, selectedStrat):
        """连接"""
        try:            
            # 创建行情和交易接口对象
            self.mdApi.connect(username, token)
            self.tdApi.connect(username, token, selectedStrat)

            # 初始化并启动查询
            self.initQuery()
        except:
            traceback.print_exc()
    
    #----------------------------------------------------------------------
    def subscribe(self, symbols):
        """订阅行情"""
        self.mdApi.subscribe(symbols)
        
    def unsubscribeAll(self):
        """订阅行情"""
        pass
        #self.mdApi.unsubscribeAll()
        
    #----------------------------------------------------------------------
    def sendOrder(self, orderReq):
        """发单"""
        self.tdApi.sendOrder(orderReq)
    
    #----------------------------------------------------------------------
    def sendBasketOrder(self, basketOrderReq):
        """"""
        return self.tdApi.sendBasketOrder(basketOrderReq)
        
    #----------------------------------------------------------------------
    def cancelOrder(self, cancelOrderReq):
        """撤单"""
        self.tdApi.cancelOrder(cancelOrderReq)
        
    #----------------------------------------------------------------------
    def qryAccount(self):
        """查询账户资金"""
        self.tdApi.qryAccount()
        
    #----------------------------------------------------------------------
    def qryPosition(self):
        """查询持仓"""
        self.tdApi.qryPosition()
        
    #----------------------------------------------------------------------
    def close(self):
        """关闭"""
        pass
        #self.tdApi.close()
        
    #----------------------------------------------------------------------
    def initQuery(self):
        """初始化连续查询"""
        if self.qryEnabled:
            # 需要循环的查询函数列表
            self.qryFunctionList = [self.qryPosition, self.qryAccount]
            
            self.qryCount = 0           # 查询触发倒计时
            self.qryTrigger = 2         # 查询触发点
            self.qryNextFunction = 0    # 上次运行的查询函数索引

            self.startQuery()
    
    #----------------------------------------------------------------------
    def query(self, event):
        """注册到事件处理引擎上的查询函数"""
        self.qryCount += 1
        
        if self.qryCount > self.qryTrigger:
            # 清空倒计时
            self.qryCount = 0
            
            # 执行查询函数
            function = self.qryFunctionList[self.qryNextFunction]
            function()
            
            # 计算下次查询函数的索引，如果超过了列表长度，则重新设为0
            self.qryNextFunction += 1
            if self.qryNextFunction == len(self.qryFunctionList):
                self.qryNextFunction = 0
    
    #----------------------------------------------------------------------
    def startQuery(self):
        """启动连续查询"""
        self.eventEngine.register(EVENT_TIMER, self.query)
    
    #----------------------------------------------------------------------
    def setQryEnabled(self, qryEnabled):
        """设置是否要启动循环查询"""
        self.qryEnabled = qryEnabled
    

########################################################################
class QuantOSTdApi(object):
    """交易API实现"""

    #----------------------------------------------------------------------
    def __init__(self, gateway, setting):
        """Constructor"""
        super(QuantOSTdApi, self).__init__()
        
        self.gateway = gateway                  # gateway对象
        self.gatewayName = gateway.gatewayName  # gateway对象名称
        
        self.api = None
        self.current_stratid = None
        self.current_user = None
        self.current_strats = None
        
        self.TradeApi = TradeApi
        
        self.setting = setting
        
        self.orderPricetypeDict = {}            # key:vtOrderID, value:algoType
    
    def changeTitle(self):
        self.gateway.changeTitle(self.current_user, self.current_stratid)
    #----------------------------------------------------------------------

    def clearAll(self):
        self.gateway.clearPosition()
        self.gateway.clearContract()
        self.gateway.unsubscribeAll()
    
    def loadContracts(self):
        """"""
        pf, msg = self.api.query_universe()
        
        if not check_return_error(pf, msg):
            self.writeLog(u'查询合约失败，错误信息：{}'.format(msg))
            return False
        
        symbols = ''
        for instcode in pf['security']:
            if len(instcode) > 0:        
                symbols += str(instcode)
                symbols += ","
        
        instruments = self.gateway.mdApi.queryInstruments(symbols)
        
        for k, d in instruments.items():
            contract = VtContractData()
            contract.gatewayName = self.gatewayName
            
            instcode = d['symbol']
            
            symbol, jzExchange = instcode.split('.')
            contract.symbol = symbol
            contract.exchange = exchangeMapReverse[jzExchange]
            contract.vtSymbol = '.'.join([contract.symbol, contract.exchange])
            contract.name = d['name']
            contract.priceTick = d['pricetick']
            contract.size = d['multiplier']
            contract.lotsize = d['buylot']
            contract.productClass = productClassMapReverse.get(int(d['inst_type']), PRODUCT_UNKNOWN)
            
            self.gateway.onContract(contract)

        # do not subscribe            
        #self.gateway.subscribe(symbols)
                
        self.writeLog(u'查询合约信息成功')
        return True

    def subscribePositionSymbols(self):
        """"""
        pf, msg = self.api.query_position()

        if not check_return_error(pf, msg):
            self.writeLog(u'查询持仓失败，错误信息：{}'.format(msg))
            return False
        
        symbols = ''
        for instcode in pf['security']:
            symbols += str(instcode)
            symbols += ","

        quotes = self.gateway.mdApi.queryQuotes(symbols)
        for k, d in quotes.items():
            tick = VtTickData()
            tick.gatewayName = self.gatewayName
            
            instcode = d['symbol']
            symbol, jzExchange = instcode.split('.')
            tick.symbol = symbol
            tick.exchange = exchangeMapReverse[jzExchange]
            tick.vtSymbol = '.'.join([symbol, jzExchange])

            tick.openPrice = d['open']
            tick.highPrice = d['high']
            tick.lowPrice = d['low']
            tick.volume = d['volume']
            tick.volchg = 0
            tick.turnover = d['turnover'] if 'turnover' in d else 0
            tick.lastPrice = d['last']
            
            tick.openInterest = d['oi'] if 'oi' in d else 0
            tick.preClosePrice = d['preclose'] if 'preclose' in d else 0
            tick.date = str(d['date'])
            
            t = str(d['time'])
            t = t.rjust(9, '0')
            tick.time = '%s:%s:%s.%s' %(t[0:2],t[2:4],t[4:6],t[6:])
            
            tick.bidPrice1 = d['bidprice1']
            tick.bidPrice2 = d['bidprice2']
            tick.bidPrice3 = d['bidprice3']
            tick.bidPrice4 = d['bidprice4']
            tick.bidPrice5 = d['bidprice5']
            
            tick.askPrice1 = d['askprice1']
            tick.askPrice2 = d['askprice2']
            tick.askPrice3 = d['askprice3']
            tick.askPrice4 = d['askprice4']
            tick.askPrice5 = d['askprice5']       
    
            tick.bidVolume1 = d['bidvolume1']
            tick.bidVolume2 = d['bidvolume2']
            tick.bidVolume3 = d['bidvolume3']
            tick.bidVolume4 = d['bidvolume4']
            tick.bidVolume5 = d['bidvolume5']
    
            tick.askVolume1 = d['askvolume1']
            tick.askVolume2 = d['askvolume2']
            tick.askVolume3 = d['askvolume3']
            tick.askVolume4 = d['askvolume4']
            tick.askVolume5 = d['askvolume5']   
            
            tick.upperLimit = d['limit_up'] if 'limit_up' in d else 0
            tick.lowerLimit = d['limit_down'] if 'limit_down' in d else 0
    
            self.gateway.onTick(tick)            
            
        self.gateway.subscribe(symbols)
                
        self.writeLog(u'订阅合约信息成功')
        return True

    #----------------------------------------------------------------------
    def onOrderStatus(self, data):
        """委托信息推送"""
        order = VtOrderData()
        order.gatewayName = self.gatewayName
    
        symbol, exchange = data['security'].split('.')
        order.symbol = symbol
        order.exchange = exchangeMapReverse.get(exchange, EXCHANGE_UNKNOWN)
        order.vtSymbol = '.'.join([order.symbol, order.exchange])
    
        order.orderID = str(data['entrust_no'])
        order.taskID = str(data['task_id'])
        order.vtOrderID = order.orderID
        
        order.direction, order.offset = actionMapReverse.get(data['entrust_action'], (DIRECTION_UNKNOWN, OFFSET_UNKNOWN))
        order.totalVolume = data['entrust_size']
        order.tradedVolume = data['fill_size']
        order.price = data['entrust_price']
        order.status = statusMapReverse.get(data['order_status'])
        
        # addtional info
        order.tradePrice = data['fill_price'] 

        t = str(data['entrust_time'])
        t = t.rjust(6, '0')
        order.orderTime = '%s:%s:%s' %(t[0:2],t[2:4],t[4:])   
        
        #if order.vtOrderID in self.orderPricetypeDict:
            #order.priceType = self.orderPricetypeDict[order.vtOrderID]
        order.priceType = data['algo']
        
        self.gateway.onOrder(order)
    
    #----------------------------------------------------------------------
    def onTaskStatus(self, data):
        """"""
        task = TaskData()
        task.taskId = str(data['task_id'])
        task.taskStatus = data['task_status']
        
        event = Event(EVENT_TASK)
        event.dict_['data'] = task
        
        self.gateway.eventEngine.put(event)
    
    #----------------------------------------------------------------------
    def onTrade(self, data):
        """成交信息推送"""
        trade = VtTradeData()
        trade.gatewayName = self.gatewayName
        
        symbol, jzExchange = data['security'].split('.')
        trade.symbol = symbol
        trade.exchange = exchangeMapReverse.get(jzExchange, EXCHANGE_UNKNOWN)
        trade.vtSymbol = '.'.join([trade.symbol, trade.exchange])
        
        trade.direction, trade.offset = actionMapReverse.get(data['entrust_action'], (DIRECTION_UNKNOWN, OFFSET_UNKNOWN))
        
        trade.tradeID = str(data['fill_no'])
        trade.vtTradeID = str(data['fill_no'])
        
        trade.orderID = str(data['entrust_no'])
        trade.vtOrderID = trade.orderID
        trade.taskID = str(data['task_id'])
        
        trade.price = data['fill_price']
        trade.volume = data['fill_size']
        
        t = str(data['fill_time'])
        t = t.rjust(6, '0')
        trade.tradeTime = '%s:%s:%s' %(t[0:2],t[2:4],t[4:])        
        
        self.gateway.onTrade(trade)
        
    #----------------------------------------------------------------------
    def onConnection(self, data):
        """"""
        self.writeLog(u'连接状态更新：%s' %data)
        
    def getStrategyList(self, username, token):
        
        if self.api is None:
            tdAddress = self.setting['tdAddress']
            self.api = self.TradeApi(tdAddress)

            # 登录
            info, msg = self.api.login(username, token)

            if check_return_error(info, msg):
                self.writeLog(u'登录成功')
                self.current_strats = info['strategies']
                self.current_user = info['username']
                return info['strategies']
            # if info is None:
            else:
                self.writeLog(u'登录失败，错误信息：%s' % msg)
                self.api = None
                return None
        else:
            self.writeLog(u'已经登录')
            return self.current_strats

    #----------------------------------------------------------------------
    def connect(self, username, password, strategyid):
        """初始化连接"""
        # 创建API对象并绑定回调函数
        if self.api is None:
            tdAddress = self.setting['tdAddress']
            self.api = self.TradeApi(tdAddress)
            # 登录
            info, msg = self.api.login(username, password)

        else:
            info = 0
        
        if info is None:
            self.writeLog(u'登录失败，错误信息：%s' %msg)
            self.api = None
        else:
            if info == 0:
                self.writeLog(u'已经登录')
            else:
                self.writeLog(u'登录成功')
                self.current_user = username
            
            if self.current_stratid is None:
                self.api.set_ordstatus_callback(self.onOrderStatus)
                self.api.set_trade_callback(self.onTrade)
                self.api.set_task_callback(self.onTaskStatus)
                self.api.set_connection_callback(self.onConnection)
                # 使用某个策略号
            
            if self.current_stratid != strategyid:
                result, msg = self.api.use_strategy(int(strategyid))
                self.current_stratid = strategyid
    
                if check_return_error(result, msg):
                    self.writeLog(u'选定策略账户%s成功' %result)
                    # sleep for 1 second and then query data
                    time.sleep(1)
                    self.changeTitle()
                    self.clearAll()
                    self.loadContracts()
                    self.subscribePositionSymbols()
                    self.qryOrder()
                    self.qryTrade()
                else:
                    self.writeLog(u'选定策略账户失败，错误信息：%s' %msg)
            else:
                    time.sleep(1)
                    self.clearAll()
                    self.loadContracts() 
                    self.subscribePositionSymbols()    
                    self.qryOrder()
                    self.qryTrade()
                    
    #----------------------------------------------------------------------
    def close(self):
        """关闭"""
        pass
            
    #----------------------------------------------------------------------
    def writeLog(self, logContent):
        """记录日志"""
        log = VtLogData()
        log.gatewayName = self.gatewayName
        log.logContent = logContent
        self.gateway.onLog(log)
    
    #----------------------------------------------------------------------
    def sendOrder(self, orderReq):
        """发单"""
        security = '.'.join([orderReq.symbol, exchangeMap.get(orderReq.exchange, '')])
        urgency = orderReq.urgency
        algo, paramsFunction = priceTypeMap[orderReq.priceType]
        
        if len(orderReq.offset) > 0:
            action = actionMap.get((orderReq.direction, orderReq.offset), '')
            if len(algo) > 0:
                taskid, msg = self.api.place_order(security, action, orderReq.price, int(orderReq.volume), algo, paramsFunction(security, urgency))
            else:
                taskid, msg = self.api.place_order(security, action, orderReq.price, int(orderReq.volume))
            
            if not check_return_error(taskid, msg):
                self.writeLog(u'委托失败，错误信息：%s' %msg)
        else:
            inc_size = int(orderReq.volume) if orderReq.direction == DIRECTION_LONG else int(orderReq.volume) * -1
                
            taskid, msg = self.api.batch_order([{"security": security, "price":orderReq.price, "size":inc_size}], algo, paramsFunction(security, urgency))
            if not check_return_error(taskid, msg):
                self.writeLog(u'篮子委托失败，错误信息：%s' %msg)
    #----------------------------------------------------------------------
    def sendBasketOrder(self, req):
        """
        when sending basket order, taskid is returned instead of vtOrderID
        """
        taskid, msg = self.api.basket_order(req.positions, req.algo, req.params)
        
        # return result
        if not check_return_error(taskid, msg):
            self.writeLog(u'篮子委托失败，错误信息：%s' %msg)
            return None
        else:     
            return str(taskid)
        
    #----------------------------------------------------------------------
    def cancelOrder(self, cancelOrderReq):
        """撤单"""
        if not self.api:
            return

        result, msg = self.api.cancel_order(cancelOrderReq.orderID)

        if not check_return_error(taskid, msg):
            self.writeLog(u'撤单失败，错误信息：%s' %msg)
            
    #----------------------------------------------------------------------
    def qryPosition(self):
        """查询持仓"""
        df, msg = self.api.query_position()
        
        if not check_return_error(df, msg):
            self.writeLog(u'查询持仓失败，错误信息：%s' %msg)
            return False
        
        for i in range(len(df)):
            data = df.loc[i]

            position = VtPositionData()
            position.gatewayName = self.gatewayName
            
            symbol, jzExchange = data.security.split('.')
            position.symbol = symbol
            position.exchange = exchangeMapReverse.get(jzExchange, EXCHANGE_UNKNOWN)
            position.vtSymbol = '.'.join([position.symbol, position.exchange])
                        
            position.direction = sideMapReverse.get(data.side, DIRECTION_UNKNOWN)
            position.vtPositionName = '.'.join([position.vtSymbol, position.direction])
            
            position.price = data.cost_price
            position.ydPosition = data.pre_size
            position.tdPosition = data.today_size
            position.position = data.current_size
            position.frozen = data.frozen_size
            
            position.commission = data.commission
            position.enable = data.enable_size  
            position.want = data.want_size
            position.initPosition = data.init_size
            position.trading = data.trading_pnl
            position.holding = data.holding_pnl
            position.last = data.last_price
            
            if (position.position > 0):
                contract = self.gateway.dataengine.getContract(position.vtSymbol)
                if (contract != None):
                    position.mktval = data.last_price * position.position * contract.size
                else:
                    position.mktval = 0.0
        
            self.gateway.onPosition(position)
        
        return True
    
    def qryAccount(self):
        
        df, msg = self.api.query_account()
        
        if not check_return_error(df, msg):
            self.writeLog(u'查询资金失败，错误信息：%s' %msg)
            return False
        
        for i in range(len(df)):
            data = df.loc[i]

            account = VtAccountData()
                
            account.accountID = data.id
            account.type = data.type
            account.vtAccountID = str(data.id) + "_" + data.type
    
            account.frozen_balance = data.frozen_balance
            account.enable_balance = data.enable_balance
            account.float_pnl = data.float_pnl
            account.init_balance = data.init_balance
            account.deposit_balance = data.deposit_balance
            account.holding_pnl = data.holding_pnl
            account.close_pnl = data.close_pnl
            account.margin = data.margin
            account.trading_pnl = data.trading_pnl
    
            self.gateway.onAccount(account)
    
    #----------------------------------------------------------------------
    def qryOrder(self):
        """查询委托"""
        df, msg = self.api.query_order()

        if not check_return_error(df, msg):
            self.writeLog(u'查询委托失败，错误信息：%s' %msg)
            return False
        
        for i in range(len(df)):
            data = df.loc[i]
            self.onOrderStatus(data)
        
        self.writeLog(u'查询委托完成')
        return True
    
    #----------------------------------------------------------------------
    def qryTrade(self):
        """查询成交"""
        df, msg = self.api.query_trade()

        if not check_return_error(df, msg):
            self.writeLog(u'查询成交失败，错误信息：%s' %msg)
            return False
        
        for i in range(len(df)):
            data = df.loc[i]
            self.onTrade(data)
            
        self.writeLog(u'查询成交完成')
        return True

    

########################################################################
class QuantOSMdApi(object):
    #----------------------------------------------------------------------
    def __init__(self, gateway, setting):
        """Constructor"""
        super(QuantOSMdApi, self).__init__()
        
        self.gateway = gateway
        self.gatewayName = gateway.gatewayName
        
        self.api = None
        
        self.fields = "OPEN,CLOSE,HIGH,LOW,LAST,\
        VOLUME,TURNOVER,OI,PRECLOSE,TIME,DATE,\
        ASKPRICE1,ASKPRICE2,ASKPRICE3,ASKPRICE4,ASKPRICE5,\
        BIDPRICE1,BIDPRICE2,BIDPRICE3,BIDPRICE4,BIDPRICE5,\
        ASKVOLUME1,ASKVOLUME2,ASKVOLUME3,ASKVOLUME4,ASKVOLUME5,\
        BIDVOLUME1,BIDVOLUME2,BIDVOLUME3,BIDVOLUME4,BIDVOLUME5,\
        LIMIT_UP,LIMIT_DOWN"
        
        self.fields = self.fields.replace(' ', '').lower()
        
        self.DataApi = DataApi

        self.setting = setting
        
    #----------------------------------------------------------------------
    def onMarketData(self, key, data):    
        """行情推送"""
        tick = VtTickData()
        tick.gatewayName = self.gatewayName
        
        try:
            l = data['symbol'].split('.')
            tick.symbol = l[0]
            tick.exchange = exchangeMapReverse.get(l[1], EXCHANGE_UNKNOWN)
            tick.vtSymbol = '.'.join([tick.symbol, tick.exchange])
            
            tick.openPrice = data['open']
            tick.highPrice = data['high']
            tick.lowPrice = data['low']
            tick.volume = data['volume']
            tick.volchg = 0
            tick.turnover = data['turnover'] if 'turnover' in data else 0
            tick.lastPrice = data['last']
            
            tick.openInterest = data['oi'] if 'oi' in data else 0
            tick.preClosePrice = data['preclose'] if 'preclose' in data else 0
            tick.date = str(data['date'])
            
            t = str(data['time'])
            t = t.rjust(9, '0')
            tick.time = '%s:%s:%s.%s' %(t[0:2],t[2:4],t[4:6],t[6:])
            
            tick.bidPrice1 = data['bidprice1']
            tick.bidPrice2 = data['bidprice2']
            tick.bidPrice3 = data['bidprice3']
            tick.bidPrice4 = data['bidprice4']
            tick.bidPrice5 = data['bidprice5']
            
            tick.askPrice1 = data['askprice1']
            tick.askPrice2 = data['askprice2']
            tick.askPrice3 = data['askprice3']
            tick.askPrice4 = data['askprice4']
            tick.askPrice5 = data['askprice5']       
    
            tick.bidVolume1 = data['bidvolume1']
            tick.bidVolume2 = data['bidvolume2']
            tick.bidVolume3 = data['bidvolume3']
            tick.bidVolume4 = data['bidvolume4']
            tick.bidVolume5 = data['bidvolume5']
    
            tick.askVolume1 = data['askvolume1']
            tick.askVolume2 = data['askvolume2']
            tick.askVolume3 = data['askvolume3']
            tick.askVolume4 = data['askvolume4']
            tick.askVolume5 = data['askvolume5']   
            
            tick.upperLimit = data['limit_up'] if 'limit_up' in data else 0
            tick.lowerLimit = data['limit_down'] if 'limit_down' in data else 0
    
            self.gateway.onTick(tick)
        except Exception as e:
            self.writeLog(u'行情更新失败，错误信息：%s' % str(e))

    #----------------------------------------------------------------------
    def connect(self, username, token):
        """ todo """
        """连接"""
        if self.api is None:

            self.api = self.DataApi(self.setting['mdAddress'])
            
            #登录
            info, msg = self.api.login(username, token)
            if check_return_error(info, msg):
                self.writeLog(u'行情连接成功')
            else:
                self.writeLog(u'行情连接失败，错误信息：%s' % msg)
        else:
            self.writeLog(u'行情已经连接')
    
    def unsubscribeAll(self):
        subscribed, msg = self.api.unsubscribe()

    #----------------------------------------------------------------------
    def subscribe(self, symbols):
        """订阅"""
        subscribed, msg = self.api.subscribe(symbols, fields=self.fields, func=self.onMarketData)
        if not check_return_error(subscribed, msg):
            self.writeLog(u'行情订阅失败，错误信息：%s' % msg)
    
    #----------------------------------------------------------------------
    def writeLog(self, logContent):
        """记录日志"""
        log = VtLogData()
        log.gatewayName = self.gatewayName
        log.logContent = logContent
        self.gateway.onLog(log)    
        
    #----------------------------------------------------------------------
    def queryInstruments(self, instcodes):

        p = "symbol=%s" %instcodes
        df, msg = self.api.query("jz.instrumentInfo", fields="symbol, name, buylot, selllot, pricetick, multiplier, inst_type", filter=p)
        
        d = {}
        if df is None:
            return {}

        for i in range(len(df)):
            k = df.iloc[i]['symbol']
            v = df.iloc[i]
            d[k] = v
        return d

    #----------------------------------------------------------------------
    def queryQuotes(self, instcodes):

        item_count = 50
        
        codelist = instcodes.split(",")
        
        d = {}
        
        symbol = ''
        for idx in range(len(codelist)):
            symbol += codelist[idx]
            symbol += ','
            
            if (idx == item_count):
                df, msg = self.api.quote(fields=self.fields, symbol=symbol)    
                
                for i in range(len(df)):
                    k = df.iloc[i]['symbol']
                    v = df.iloc[i]
                    d[k] = v

                idx = 0
                
        if idx>0:
            df, msg = self.api.quote(fields=self.fields, symbol=symbol)    
            
            for i in range(len(df)):
                k = df.iloc[i]['symbol']
                v = df.iloc[i]
                d[k] = v
            
        return d


########################################################################
class TaskData(object):
    """"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self.taskId = EMPTY_STRING
        self.taskStatus = EMPTY_UNICODE
        
    
    

