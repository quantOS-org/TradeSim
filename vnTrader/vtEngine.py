# encoding: UTF-8

from builtins import object


import shelve
from collections import OrderedDict

from eventEngine import *
from vtGateway import *


########################################################################
class MainEngine(object):
    """主引擎"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        # 创建事件引擎
        self.eventEngine = EventEngine2()
        self.eventEngine.start()
        
        # 创建数据引擎
        self.dataEngine = DataEngine(self.eventEngine)
        
        # 调用一个个初始化函数
        self.initGateway()

    #----------------------------------------------------------------------
    def initGateway(self):
        """初始化接口对象"""
        # 用来保存接口对象的字典
        self.gatewayDict = OrderedDict()
        
        # 创建我们想要接入的接口对象
        from gateway.quantosGateway import QuantOSGateway
        self.addGateway(QuantOSGateway, 'quantos')
        self.gatewayDict['quantos'].setQryEnabled(True)   

    #----------------------------------------------------------------------
    def addGateway(self, gateway, gatewayName=None):
        """创建接口"""
        self.gatewayDict[gatewayName] = gateway(self.eventEngine, self.dataEngine, gatewayName)
        
    #----------------------------------------------------------------------
    def connect(self, gatewayName):
        """连接特定名称的接口"""
        if gatewayName in self.gatewayDict:
            gateway = self.gatewayDict[gatewayName]
            gateway.connect()
        else:
            self.writeLog(u'接口不存在：%s' %gatewayName)
        
    #----------------------------------------------------------------------
    def subscribe(self, symbols, gatewayName):
        """订阅特定接口的行情"""
        if gatewayName in self.gatewayDict:
            gateway = self.gatewayDict[gatewayName]
            gateway.subscribe(symbols)
        else:
            self.writeLog(u'接口不存在：%s' %gatewayName)        
        
    #----------------------------------------------------------------------
    def sendOrder(self, orderReq, gatewayName):
        """对特定接口发单"""
        if gatewayName in self.gatewayDict:
            gateway = self.gatewayDict[gatewayName]
            gateway.sendOrder(orderReq)
        else:
            self.writeLog(u'接口不存在：%s' %gatewayName)  
            
    #----------------------------------------------------------------------
    def sendBasketOrder(self, req):
        """"""
        gatewayName = 'quantos'
        if gatewayName in self.gatewayDict:
            gateway = self.gatewayDict[gatewayName]
            return gateway.sendBasketOrder(req)
        else:
            self.writeLog(u'接口不存在：%s' %gatewayName)        
    
    #----------------------------------------------------------------------
    def cancelOrder(self, cancelOrderReq, gatewayName):
        """对特定接口撤单"""
        if gatewayName in self.gatewayDict:
            gateway = self.gatewayDict[gatewayName]
            gateway.cancelOrder(cancelOrderReq)
        else:
            self.writeLog(u'接口不存在：%s' %gatewayName)        
        
    #----------------------------------------------------------------------
    def qryAccount(self, gatewayName):
        """查询特定接口的账户"""
        if gatewayName in self.gatewayDict:
            gateway = self.gatewayDict[gatewayName]
            gateway.qryAccount()
        else:
            self.writeLog(u'接口不存在：%s' %gatewayName)        
        
    #----------------------------------------------------------------------
    def qryPosition(self, gatewayName):
        """查询特定接口的持仓"""
        if gatewayName in self.gatewayDict:
            gateway = self.gatewayDict[gatewayName]
            gateway.qryPosition()
        else:
            self.writeLog(u'接口不存在：%s' %gatewayName)        
        
    #----------------------------------------------------------------------
    def exit(self):
        """退出程序前调用，保证正常退出"""        
        # 安全关闭所有接口
        for gateway in list(self.gatewayDict.values()):        
            gateway.close()
        
        # 停止事件引擎
        self.eventEngine.stop()      
        
    #----------------------------------------------------------------------
    def writeLog(self, content):
        """快速发出日志事件"""
        log = VtLogData()
        log.logContent = content
        event = Event(type_=EVENT_LOG)
        event.dict_['data'] = log
        self.eventEngine.put(event)        
    
    #----------------------------------------------------------------------
    def getContract(self, symbol):
        """查询合约"""
        return self.dataEngine.getContract(symbol)
    
    #----------------------------------------------------------------------
    def getAllContracts(self):
        """查询所有合约（返回列表）"""
        return self.dataEngine.getAllContracts()
    
    #----------------------------------------------------------------------
    def getOrder(self, vtOrderID):
        """查询委托"""
        return self.dataEngine.getOrder(vtOrderID)
    
    #----------------------------------------------------------------------
    def getAllWorkingOrders(self):
        """查询所有的活跃的委托（返回列表）"""
        return self.dataEngine.getAllWorkingOrders()
    
    #----------------------------------------------------------------------
    def getAllOrders(self):
        """"""
        return self.dataEngine.getAllOrders()
        
    

########################################################################
class DataEngine(object):
    """数据引擎"""
    #----------------------------------------------------------------------
    def __init__(self, eventEngine):
        """Constructor"""
        self.eventEngine = eventEngine
        
        # 保存合约详细信息的字典
        self.contractDict = {}
        
        # 保存委托数据的字典
        self.orderDict = {}
        
        # 保存活动委托数据的字典（即可撤销）
        self.workingOrderDict = {}
        
        # 注册事件监听
        self.registerEvent()
        
    #----------------------------------------------------------------------
    def updateContract(self, event):
        """更新合约数据"""
        contract = event.dict_['data']
        self.contractDict[contract.symbol] = contract

    def clearContract(self, event):
        self.contractDict.clear()
              
    #----------------------------------------------------------------------
    def getContract(self, symbol):
        """查询合约对象"""
        try:
            return self.contractDict[symbol]
        except KeyError:
            return None
        
    #----------------------------------------------------------------------
    def getAllContracts(self):
        """查询所有合约对象（返回列表）"""
        return list(self.contractDict.values())
    
    #----------------------------------------------------------------------
    def updateOrder(self, event):
        """更新委托数据"""
        order = event.dict_['data']        
        self.orderDict[order.vtOrderID] = order
        
        # 如果订单的状态是全部成交或者撤销，则需要从workingOrderDict中移除
        if order.status in (STATUS_ALLTRADED, STATUS_CANCELLED, STATUS_REJECTED):
            if order.vtOrderID in self.workingOrderDict:
                del self.workingOrderDict[order.vtOrderID]
        # 否则则更新字典中的数据        
        else:
            self.workingOrderDict[order.vtOrderID] = order
    
    #----------------------------------------------------------------------
    def getOrder(self, vtOrderID):
        """查询委托"""
        try:
            return self.orderDict[vtOrderID]
        except KeyError:
            return None
    
    #----------------------------------------------------------------------
    def getAllWorkingOrders(self):
        """查询所有活动委托（返回列表）"""
        return list(self.workingOrderDict.values())
    
    #----------------------------------------------------------------------
    def getAllOrders(self):
        """"""
        return list(self.orderDict.values())
    
    #----------------------------------------------------------------------
    def registerEvent(self):
        """注册事件监听"""
        self.eventEngine.register(EVENT_CONTRACT, self.updateContract)
        self.eventEngine.register(EVENT_CONTRACT_CLEAR, self.clearContract)
        self.eventEngine.register(EVENT_ORDER, self.updateOrder)
        
    
    
