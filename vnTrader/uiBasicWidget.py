# encoding: UTF-8

# import json
from __future__ import division

import csv
from builtins import range
from builtins import str
from collections import OrderedDict

from past.utils import old_div

# PyQt 4/5 compatibility
try:
    from PyQt4.QtGui import QTableWidgetItem, QTableWidget, QFrame, QLabel, QLineEdit, QComboBox, QDoubleSpinBox, \
        QSpinBox, QCheckBox, QGridLayout, QHBoxLayout, QVBoxLayout, QPushButton, QMenu, QAction, QHeaderView
    from PyQt4 import QtGui, QtCore
except ImportError:
    from PyQt5 import QtGui, QtCore
    from PyQt5.QtWidgets import QTableWidgetItem, QTableWidget, QFrame, QLabel, QLineEdit, QComboBox, QDoubleSpinBox, \
        QSpinBox, QCheckBox, QGridLayout, QHBoxLayout, QVBoxLayout, QPushButton, QMenu, QAction, QHeaderView

from eventEngine import *
from vtFunction import *
from vtGateway import *


# ----------------------------------------------------------------------
def loadFont():
    """载入字体设置"""
    try:
        f = file("setting/VT_setting.json")
        setting = json.load(f)
        family = setting['fontFamily']
        size = setting['fontSize']
        font = QtGui.QFont(family, size)
    except:
        font = QtGui.QFont(u'微软雅黑', 12)
    return font


BASIC_FONT = loadFont()


########################################################################
class BasicCell(QTableWidgetItem):
    """基础的单元格"""
    
    # ----------------------------------------------------------------------
    def __init__(self, text=None, mainEngine=None, foreground=None, background=None):
        """Constructor"""
        super(BasicCell, self).__init__()
        if foreground is not None:
            self.setForeground(foreground)
        if background is not None:
            self.setBackground(background)
            
        self.data = None
        if text:
            self.setContent(text)
    
    def _conditional_style_before(self, text):
        pass

    def _conditional_style_after(self, text):
        pass
    
    def _after_set_text(self):
        pass
    
    def _get_text(self, text):
        return text
    
    # ----------------------------------------------------------------------
    def setContent(self, text):
        """设置内容"""
        
        if text is None:
            self.setText("")
            return
        
        real_text = self._get_text(text)
        
        self._conditional_style_before(text)
        self.setText(real_text)
        self._conditional_style_after(text)
        
        self._after_set_text()


class ErrorCell(BasicCell):
    """基础的单元格"""
    
    def _conditional_style_after(self, text):
        if text.find(u'失败') >= 0 or text.find(u'错误') >= 0:
            self.setForeground(QtGui.QColor('red'))
            self.setToolTip(text)


########################################################################
class NumCell(BasicCell):
    """用来显示数字的单元格"""
    
    def _get_text(self, text):
        if text == '0' or text == '0.0':
            res = ''
        else:
            res = text
        return res


########################################################################
class NumCellColored(NumCell):
    """用来显示数字的单元格"""
    
    def _conditional_style_after(self, text):
        try:
            num = float(text)
        except Exception as e:
            print(type(text), text)
            raise(e)
        if num < 0:
            self.setForeground(QtGui.QColor('green'))
        else:
            self.setForeground(QtGui.QColor('red'))


class PositionCell(NumCell):
    """用来显示数字的单元格"""
    pass
    

########################################################################
class DirectionCell(BasicCell):
    """用来显示买卖方向的单元格"""
    
    # ----------------------------------------------------------------------
    def _conditional_style_after(self, text):
        """设置内容"""
        if text == DIRECTION_LONG or text == DIRECTION_NET:
            self.setForeground(QtGui.QColor('red'))
        elif text == DIRECTION_SHORT:
            self.setForeground(QtGui.QColor('green'))


########################################################################
class NameCell(BasicCell):
    """用来显示合约中文的单元格"""
    
    # ----------------------------------------------------------------------
    def __init__(self, text=None, mainEngine=None):
        """Constructor"""
        self.mainEngine = mainEngine
        
        super(NameCell, self).__init__(text=text, mainEngine=mainEngine)
        
        
    def _get_text(self, text):
        if self.mainEngine:
            # 首先尝试正常获取合约对象
            contract = self.mainEngine.getContract(text)
        
            # 如果能读取合约信息
            if contract:
                return contract.name
        

########################################################################
class BidCell(BasicCell):
    """买价单元格"""
    
    # ----------------------------------------------------------------------
    def __init__(self, text=None, mainEngine=None):
        """Constructor"""
        super(BidCell, self).__init__(text=text, mainEngine=mainEngine,
                                      background=QtGui.QColor(255, 174, 201),
                                      foreground=QtGui.QColor('black'))


########################################################################
class AskCell(BasicCell):
    """买价单元格"""
    
    # ----------------------------------------------------------------------
    def __init__(self, text=None, mainEngine=None):
        """Constructor"""
        super(AskCell, self).__init__(text=text, mainEngine=mainEngine,
                                      background=QtGui.QColor(160, 255, 160),
                                      foreground=QtGui.QColor('black'))


########################################################################
class BasicMonitor(QTableWidget):
    """
    基础监控
    
    headerDict中的值对应的字典格式如下
    {'chinese': u'中文名', 'cellType': BasicCell}
    
    """
    signal = QtCore.pyqtSignal(type(Event()))
    signal_clear = QtCore.pyqtSignal(type(Event()))
    
    # ----------------------------------------------------------------------
    def __init__(self, mainEngine=None, eventEngine=None, parent=None):
        """Constructor"""
        super(BasicMonitor, self).__init__(parent)
        
        self.mainEngine = mainEngine
        self.eventEngine = eventEngine
        
        self.signalemit = None
        self.signalclearemit = None
        
        # 保存表头标签用
        self.headerDict = OrderedDict()  # 有序字典，key是英文名，value是对应的配置字典
        self.headerList = []  # 对应self.headerDict.keys()
        
        # 保存相关数据用
        self.dataDict = {}  # 字典，key是字段对应的数据，value是保存相关单元格的字典
        self.dataKey = ''  # 字典键对应的数据字段
        
        # 监控的事件类型
        self.eventType = ''
        self.eventTypeClear = ''
        # 字体
        self.font = None
        
        # 保存数据对象到单元格
        self.saveData = False
        
        # 默认不允许根据表头进行排序，需要的组件可以开启
        self.sorting = False
        
        # 初始化右键菜单
        self.initMenu()
    
    # ----------------------------------------------------------------------
    def setHeaderDict(self, headerDict):
        """设置表头有序字典"""
        self.headerDict = headerDict
        self.headerList = list(headerDict.keys())
    
    # ----------------------------------------------------------------------
    def setDataKey(self, dataKey):
        """设置数据字典的键"""
        self.dataKey = dataKey
    
    # ----------------------------------------------------------------------
    def setEventType(self, eventType1, eventType2=''):
        """设置监控的事件类型"""
        self.eventType = eventType1
        self.eventTypeClear = eventType2
    
    # ----------------------------------------------------------------------
    def setFont(self, font):
        """设置字体"""
        self.font = font
    
    # ----------------------------------------------------------------------
    def setSaveData(self, saveData):
        """设置是否要保存数据到单元格"""
        self.saveData = saveData
    
    # ----------------------------------------------------------------------
    def initTable(self):
        """初始化表格"""
        # 设置表格的列数
        col = len(self.headerDict)
        self.setColumnCount(col)
        
        # 设置列表头
        labels = [d['chinese'] for d in list(self.headerDict.values())]
        self.setHorizontalHeaderLabels(labels)
        
        # 关闭左边的垂直表头
        self.verticalHeader().setVisible(False)
        
        # 设为不可编辑
        self.setEditTriggers(self.NoEditTriggers)
        
        # 设为行交替颜色
        self.setAlternatingRowColors(True)
        
        # 设置允许排序
        self.setSortingEnabled(self.sorting)
        
        # set stretch
        # self.horizontalHeader().setResizeMode(QHeaderView.Stretch)
    
    # ----------------------------------------------------------------------
    def registerEvent(self):
        """注册GUI更新相关的事件监听"""
        self.signal.connect(self.updateEvent)
        self.signalemit = self.signal.emit
        self.eventEngine.register(self.eventType, self.signalemit)
        if len(self.eventTypeClear) > 0:
            self.signal_clear.connect(self.clearEvent)
            self.signalclearemit = self.signal_clear.emit
            self.eventEngine.register(self.eventTypeClear, self.signalclearemit)
    
    def unRegister(self):
        self.eventEngine.unregister(self.eventType, self.signalemit)
        if len(self.eventTypeClear) > 0:
            self.eventEngine.unregister(self.eventTypeClear, self.signalclearemit)
    
    # ----------------------------------------------------------------------
    def updateEvent(self, event):
        """收到事件更新"""
        data = event.dict_['data']
        self.updateData(data)
    
    def clearEvent(self, event):
        """收到事件更新"""
        self.dataDict.clear()
        self.setRowCount(0)
    
    # ----------------------------------------------------------------------
    def updateData(self, data):
        """将数据更新到表格中"""
        # 如果允许了排序功能，则插入数据前必须关闭，否则插入新的数据会变乱
        if self.sorting:
            self.setSortingEnabled(False)
        
        # 如果设置了dataKey，则采用存量更新模式
        if self.dataKey:
            #key = data.__getattribute__(self.dataKey)
            key = getattr(data, self.dataKey, None)
            # 如果键在数据字典中不存在，则先插入新的一行，并创建对应单元格
            if key not in self.dataDict:
                self.insertRow(0)
                d = {}
                for n, header in enumerate(self.headerList):
                    content = safeUnicode(data.__getattribute__(header))
                    # content = safeUnicode(getattr(data, header, None))
                    cellType = self.headerDict[header]['cellType']
                    try:
                        cell = cellType(content, self.mainEngine)
                    except Exception as e:
                        print(cellType)
                        print(data)
                        print(content)
                        raise(e)
                    
                    if self.font:
                        cell.setFont(self.font)  # 如果设置了特殊字体，则进行单元格设置
                    
                    if self.saveData:  # 如果设置了保存数据对象，则进行对象保存
                        cell.data = data
                    
                    self.setItem(0, n, cell)
                    d[header] = cell
                self.dataDict[key] = d
            # 否则如果已经存在，则直接更新相关单元格
            else:
                d = self.dataDict[key]
                for header in self.headerList:
                    content = safeUnicode(getattr(data, header, None))
                    cell = d[header]
                    cell.setContent(content)
                    
                    if self.saveData:  # 如果设置了保存数据对象，则进行对象保存
                        cell.data = data
                        # 否则采用增量更新模式
        else:
            self.insertRow(0)
            for n, header in enumerate(self.headerList):
                content = safeUnicode(data.__getattribute__(header))
                cellType = self.headerDict[header]['cellType']
                cell = cellType(content, self.mainEngine)
                
                if self.font:
                    cell.setFont(self.font)
                
                if self.saveData:
                    cell.data = data
                
                self.setItem(0, n, cell)
                
                # 调整列宽
        self.resizeColumns()
        
        # 重新打开排序
        if self.sorting:
            self.setSortingEnabled(True)
    
    # ----------------------------------------------------------------------
    def resizeColumns(self):
        """调整各列的大小"""
        self.horizontalHeader().resizeSections(QHeaderView.ResizeToContents)
    
    # ----------------------------------------------------------------------
    def setSorting(self, sorting):
        """设置是否允许根据表头排序"""
        self.sorting = sorting
    
    # ----------------------------------------------------------------------
    def saveToCsv(self):
        """保存表格内容到CSV文件"""
        # 先隐藏右键菜单
        self.menu.close()
        
        # 获取想要保存的文件名
        path = QtGui.QFileDialog.getSaveFileName(self, '保存数据', '', 'CSV(*.csv)')
        
        try:
            if not path.isEmpty():
                with open(safeUnicode(path), 'wb') as f:
                    writer = csv.writer(f)
                    
                    # 保存标签
                    headers = [header.encode('gbk') for header in self.headerList]
                    writer.writerow(headers)
                    
                    # 保存每行内容
                    for row in range(self.rowCount()):
                        rowdata = []
                        for column in range(self.columnCount()):
                            item = self.item(row, column)
                            if item is not None:
                                rowdata.append(
                                        safeUnicode(item.text()).encode('gbk'))
                            else:
                                rowdata.append('')
                        writer.writerow(rowdata)
        except IOError:
            pass
    
    # ----------------------------------------------------------------------
    def initMenu(self):
        """初始化右键菜单"""
        self.menu = QMenu(self)
        
        saveAction = QAction(u'保存内容', self)
        saveAction.triggered.connect(self.saveToCsv)
        
        resizeAction = QAction(u'调整列宽', self)
        resizeAction.triggered.connect(self.resizeColumns)
        
        self.menu.addAction(resizeAction)
        self.menu.addAction(saveAction)
    
    # ----------------------------------------------------------------------
    def contextMenuEvent(self, event):
        """右键点击事件"""
        self.menu.popup(QtGui.QCursor.pos())
    
    ########################################################################


class MarketMonitor(BasicMonitor):
    """市场监控组件"""
    
    # ----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine, parent=None):
        """Constructor"""
        super(MarketMonitor, self).__init__(mainEngine, eventEngine, parent)
        
        # 设置表头有序字典
        d = OrderedDict()
        d['symbol'] = {'chinese': u'合约代码', 'cellType': BasicCell}
        d['vtSymbol'] = {'chinese': u'名称', 'cellType': NameCell}
        d['lastPrice'] = {'chinese': u'最新价', 'cellType': BasicCell}
        d['preClosePrice'] = {'chinese': u'昨收盘价', 'cellType': BasicCell}
        d['volume'] = {'chinese': u'成交量', 'cellType': NumCell}
        d['openInterest'] = {'chinese': u'持仓量', 'cellType': NumCell}
        d['openPrice'] = {'chinese': u'开盘价', 'cellType': BasicCell}
        d['highPrice'] = {'chinese': u'最高价', 'cellType': BasicCell}
        d['lowPrice'] = {'chinese': u'最低价', 'cellType': BasicCell}
        d['bidPrice1'] = {'chinese': u'买一价', 'cellType': BidCell}
        d['bidVolume1'] = {'chinese': u'买一量', 'cellType': NumCell}
        d['askPrice1'] = {'chinese': u'卖一价', 'cellType': AskCell}
        d['askVolume1'] = {'chinese': u'卖一量', 'cellType': NumCell}
        d['time'] = {'chinese': u'时间', 'cellType': BasicCell}
        d['volchg'] = {'chinese': u'成交量变', 'cellType': NumCell}
        d['turnover'] = {'chinese': u'成交额', 'cellType': BasicCell}
        # d['gatewayName'] = {'chinese':u'接口', 'cellType':BasicCell}
        self.setHeaderDict(d)
        
        # 设置数据键
        self.setDataKey('vtSymbol')
        
        # 设置监控事件类型
        self.setEventType(EVENT_TICK, EVENT_CLEAR)
        
        # 设置字体
        self.setFont(BASIC_FONT)
        
        # 设置允许排序
        self.setSorting(False)
        self.setSaveData(True)
        
        # 初始化表格
        self.initTable()
        
        # 注册事件监听
        self.registerEvent()
    
    def updateEvent(self, event):
        new_tick = event.dict_['data']
        
        if new_tick.vtSymbol in self.dataDict:
            old_tick = self.dataDict[new_tick.vtSymbol]['symbol'].data
            new_tick.volchg = new_tick.volume - old_tick.volume if new_tick.volume > old_tick.volume else old_tick.volchg
        
        BasicMonitor.updateEvent(self, event)


########################################################################

class LogMonitor(BasicMonitor):
    """日志监控"""
    
    # ----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine, parent=None):
        """Constructor"""
        super(LogMonitor, self).__init__(mainEngine, eventEngine, parent)
        
        d = OrderedDict()
        d['logTime'] = {'chinese': u'时间', 'cellType': BasicCell}
        d['logContent'] = {'chinese': u'内容', 'cellType': ErrorCell}
        d['gatewayName'] = {'chinese': u'接口', 'cellType': BasicCell}
        self.setHeaderDict(d)
        
        self.setEventType(EVENT_LOG)
        self.setFont(BASIC_FONT)
        self.initTable()
        self.registerEvent()


########################################################################
class ErrorMonitor(BasicMonitor):
    """错误监控"""
    
    # ----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine, parent=None):
        """Constructor"""
        super(ErrorMonitor, self).__init__(mainEngine, eventEngine, parent)
        
        d = OrderedDict()
        d['errorTime'] = {'chinese': u'错误时间', 'cellType': BasicCell}
        d['errorID'] = {'chinese': u'错误代码', 'cellType': BasicCell}
        d['errorMsg'] = {'chinese': u'错误信息', 'cellType': BasicCell}
        d['additionalInfo'] = {'chinese': u'补充信息', 'cellType': BasicCell}
        d['gatewayName'] = {'chinese': u'接口', 'cellType': BasicCell}
        self.setHeaderDict(d)
        
        self.setEventType(EVENT_ERROR)
        self.setFont(BASIC_FONT)
        self.initTable()
        self.registerEvent()


########################################################################
class TradeMonitor(BasicMonitor):
    """成交监控"""
    
    # ----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine, parent=None):
        """Constructor"""
        super(TradeMonitor, self).__init__(mainEngine, eventEngine, parent)
        
        d = OrderedDict()
        d['tradeID'] = {'chinese': u'成交编号', 'cellType': BasicCell}
        d['orderID'] = {'chinese': u'委托编号', 'cellType': BasicCell}
        d['symbol'] = {'chinese': u'合约代码', 'cellType': BasicCell}
        d['vtSymbol'] = {'chinese': u'名称', 'cellType': NameCell}
        d['direction'] = {'chinese': u'方向', 'cellType': DirectionCell}
        d['offset'] = {'chinese': u'开平', 'cellType': BasicCell}
        d['price'] = {'chinese': u'价格', 'cellType': BasicCell}
        d['volume'] = {'chinese': u'数量', 'cellType': NumCell}
        d['tradeTime'] = {'chinese': u'成交时间', 'cellType': BasicCell}
        # d['gatewayName'] = {'chinese':u'接口', 'cellType':BasicCell}
        self.setHeaderDict(d)
        
        self.setDataKey('vtTradeID')
        self.setEventType(EVENT_TRADE, EVENT_CLEAR)
        self.setFont(BASIC_FONT)
        self.setSorting(True)
        
        self.initTable()
        self.registerEvent()


########################################################################
class OrderMonitor(BasicMonitor):
    """委托监控"""
    signal_trade = QtCore.pyqtSignal(type(Event()))
    
    # ----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine, parent=None):
        """Constructor"""
        super(OrderMonitor, self).__init__(mainEngine, eventEngine, parent)
        
        self.mainEngine = mainEngine
        
        d = OrderedDict()
        d['orderID'] = {'chinese': u'委托编号', 'cellType': BasicCell}
        d['symbol'] = {'chinese': u'合约代码', 'cellType': BasicCell}
        d['vtSymbol'] = {'chinese': u'名称', 'cellType': NameCell}
        d['priceType'] = {'chinese': u'算法', 'cellType': BasicCell}
        d['direction'] = {'chinese': u'方向', 'cellType': DirectionCell}
        d['offset'] = {'chinese': u'开平', 'cellType': BasicCell}
        d['price'] = {'chinese': u'价格', 'cellType': BasicCell}
        d['totalVolume'] = {'chinese': u'委托数量', 'cellType': NumCell}
        d['tradePrice'] = {'chinese': u'成交价格', 'cellType': BasicCell}
        d['tradedVolume'] = {'chinese': u'成交数量', 'cellType': NumCell}
        d['status'] = {'chinese': u'状态', 'cellType': BasicCell}
        d['orderTime'] = {'chinese': u'委托时间', 'cellType': BasicCell}
        d['taskID'] = {'chinese': u'任务编号', 'cellType': BasicCell}
        # d['cancelTime'] = {'chinese':u'撤销时间', 'cellType':BasicCell}
        # d['frontID'] = {'chinese':u'前置编号', 'cellType':BasicCell}
        # d['sessionID'] = {'chinese':u'会话编号', 'cellType':BasicCell}
        # d['gatewayName'] = {'chinese':u'接口', 'cellType':BasicCell}
        self.setHeaderDict(d)
        
        self.setDataKey('vtOrderID')
        self.setEventType(EVENT_ORDER, EVENT_CLEAR)
        self.setFont(BASIC_FONT)
        self.setSaveData(True)
        self.setSorting(True)
        
        self.initTable()
        self.registerEvent()
        self.connectSignal()
        self.registerTradeEvent()
    
    def registerTradeEvent(self):
        self.signal_trade.connect(self.updateTrade)
        self.eventEngine.register(EVENT_TRADE, self.signal_trade.emit)
    
    # ----------------------------------------------------------------------
    def connectSignal(self):
        """连接信号"""
        # 双击单元格撤单
        self.itemDoubleClicked.connect(self.cancelOrder)
        
        # ----------------------------------------------------------------------
    
    def cancelOrder(self, cell):
        """根据单元格的数据撤单"""
        order = cell.data
        
        req = VtCancelOrderReq()
        req.symbol = order.symbol
        req.exchange = order.exchange
        req.frontID = order.frontID
        req.sessionID = order.sessionID
        req.orderID = order.taskID
        self.mainEngine.cancelOrder(req, order.gatewayName)
    
    def updateTrade(self, event):
        """更新成交数据"""
        trade = event.dict_['data']
        
        if trade.vtOrderID in self.dataDict:
            order = self.dataDict[trade.vtOrderID]['orderID'].data
            if order.status not in (STATUS_ALLTRADED, STATUS_CANCELLED, STATUS_REJECTED):
                order.tradePrice = old_div((trade.volume * trade.price + order.tradePrice * order.tradedVolume),
                                           (order.tradedVolume + trade.volume))
                order.tradedVolume += trade.volume
                self.updateData(order)


########################################################################
class PositionMonitor(BasicMonitor):
    """持仓监控"""
    
    # ----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine, parent=None):
        """Constructor"""
        super(PositionMonitor, self).__init__(mainEngine, eventEngine, parent)
        
        d = OrderedDict()
        d['symbol'] = {'chinese': u'代码', 'cellType': BasicCell}
        d['vtSymbol'] = {'chinese': u'名称', 'cellType': NameCell}
        d['direction'] = {'chinese': u'方向', 'cellType': DirectionCell}
        d['initPosition'] = {'chinese': u'初持仓', 'cellType': PositionCell}
        d['position'] = {'chinese': u'总持仓', 'cellType': PositionCell}
        d['price'] = {'chinese': u'成本价', 'cellType': NumCell}
        d['ydPosition'] = {'chinese': u'昨持仓', 'cellType': PositionCell}
        d['tdPosition'] = {'chinese': u'今持仓', 'cellType': PositionCell}
        d['frozen'] = {'chinese': u'冻结量', 'cellType': NumCell}
        d['enable'] = {'chinese': u'可用量', 'cellType': NumCell}
        d['want'] = {'chinese': u'开仓在途', 'cellType': NumCell}
        d['trading'] = {'chinese': u'交易赢亏', 'cellType': NumCellColored}
        d['holding'] = {'chinese': u'持仓赢亏', 'cellType': NumCellColored}
        d['commission'] = {'chinese': u'手续费', 'cellType': NumCell}
        
        d['last'] = {'chinese': u'市场价', 'cellType': NumCell}
        d['mktval'] = {'chinese': u'市值', 'cellType': NumCell}
        
        self.setHeaderDict(d)
        
        self.setDataKey('vtPositionName')
        self.setEventType(EVENT_POSITION, EVENT_CLEAR)
        self.setFont(BASIC_FONT)
        self.setSaveData(True)
        self.setSorting(True)
        
        self.initTable()
        self.registerEvent()
    

########################################################################
class AccountMonitor(BasicMonitor):
    """账户监控"""
    
    # ----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine, parent=None):
        """Constructor"""
        super(AccountMonitor, self).__init__(mainEngine, eventEngine, parent)
        
        d = OrderedDict()
        d['accountID'] = {'chinese': u'账号', 'cellType': BasicCell}
        d['type'] = {'chinese': u'类型', 'cellType': BasicCell}
        d['init_balance'] = {'chinese': u'期初', 'cellType': NumCell}
        d['enable_balance'] = {'chinese': u'可用', 'cellType': NumCell}
        d['frozen_balance'] = {'chinese': u'冻结', 'cellType': NumCell}
        d['margin'] = {'chinese': u'保证金', 'cellType': NumCell}
        d['holding_pnl'] = {'chinese': u'持仓盈亏', 'cellType': NumCellColored}
        d['trading_pnl'] = {'chinese': u'交易盈亏', 'cellType': NumCellColored}
        d['commission'] = {'chinese': u'手续费', 'cellType': NumCell}
        d['float_pnl'] = {'chinese': u'浮动盈亏', 'cellType': NumCellColored}
        d['close_pnl'] = {'chinese': u'平仓盈亏', 'cellType': NumCellColored}
        d['deposit_balance'] = {'chinese': u'差额', 'cellType': NumCell}
        self.setHeaderDict(d)
        
        self.setDataKey('vtAccountID')
        self.setEventType(EVENT_ACCOUNT, EVENT_CLEAR)
        self.setFont(BASIC_FONT)
        self.initTable()
        self.registerEvent()


########################################################################
class TradingWidget(QFrame):
    """简单交易组件"""
    signal = QtCore.pyqtSignal(type(Event()))
    
    directionList = [DIRECTION_LONG,
                     DIRECTION_SHORT]
    
    offsetList = [OFFSET_OPEN,
                  OFFSET_CLOSE,
                  OFFSET_CLOSEYESTERDAY,
                  OFFSET_CLOSETODAY]
    
    priceTypeList = [PRICETYPE_LIMITPRICE,
                     PRICETYPE_VWAP,
                     PRICETYPE_TWAP]
    
    exchangeList = [EXCHANGE_NONE,
                    EXCHANGE_CFFEX,
                    EXCHANGE_SHFE,
                    EXCHANGE_DCE,
                    EXCHANGE_CZCE,
                    EXCHANGE_SSE,
                    EXCHANGE_SZSE,
                    EXCHANGE_SGE,
                    EXCHANGE_HKEX,
                    EXCHANGE_SMART,
                    EXCHANGE_ICE,
                    EXCHANGE_CME,
                    EXCHANGE_NYMEX,
                    EXCHANGE_GLOBEX,
                    EXCHANGE_IDEALPRO]
    
    currencyList = [CURRENCY_NONE,
                    CURRENCY_CNY,
                    CURRENCY_USD]
    
    productClassList = [PRODUCT_NONE,
                        PRODUCT_EQUITY,
                        PRODUCT_FUTURES,
                        PRODUCT_OPTION,
                        PRODUCT_BOND,
                        PRODUCT_FOREX]
    
    # ----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine, parent=None):
        """Constructor"""
        super(TradingWidget, self).__init__(parent)
        self.mainEngine = mainEngine
        self.eventEngine = eventEngine
        
        self.symbol = ''
        self.signalemit = None
        
        self.initUi()
        self.connectSignal()
    
    # ----------------------------------------------------------------------
    def initUi(self):
        """初始化界面"""
        self.setWindowTitle(u'交易')
        self.setMaximumWidth(500)
        self.setFrameShape(self.Box)  # 设置边框
        self.setLineWidth(1)
        
        # 左边部分
        labelSymbol = QLabel(u'代码')
        labelName = QLabel(u'名称')
        labelDirection = QLabel(u'方向类型')
        labelOffset = QLabel(u'开平')
        labelPrice = QLabel(u'价格')
        labelVolume = QLabel(u'数量')
        labelPriceType = QLabel(u'价格类型')
        labelExchange = QLabel(u'交易所')
        labelCurrency = QLabel(u'货币')
        labelProductClass = QLabel(u'产品类型')
        labelUrgency = QLabel(u'紧急度')
        
        self.lineSymbol = QLineEdit()
        self.lineName = QLineEdit()
        
        self.comboDirection = QComboBox()
        self.comboDirection.addItems(self.directionList)
        
        self.comboOffset = QComboBox()
        self.comboOffset.addItem('')
        self.comboOffset.addItems(self.offsetList)
        self.comboOffset.setEnabled(False)
        
        self.tickOffset = QCheckBox(u'指定')
        
        self.spinPrice = QDoubleSpinBox()
        self.spinPrice.setDecimals(4)
        self.spinPrice.setMinimum(0)
        self.spinPrice.setMaximum(100000)
        
        self.spinVolume = QSpinBox()
        self.spinVolume.setMinimum(0)
        self.spinVolume.setMaximum(1000000)
        
        self.comboPriceType = QComboBox()
        self.comboPriceType.addItems(self.priceTypeList)
        
        self.comboExchange = QComboBox()
        self.comboExchange.addItems(self.exchangeList)
        self.comboExchange.setEnabled(False)
        
        self.comboCurrency = QComboBox()
        self.comboCurrency.addItems(self.currencyList)
        self.comboCurrency.setEnabled(False)
        
        self.comboProductClass = QComboBox()
        self.comboProductClass.addItems(self.productClassList)
        self.comboProductClass.setEnabled(False)
        
        self.spinUrgency = QSpinBox()
        self.spinUrgency.setMinimum(1)
        self.spinUrgency.setMaximum(9)
        self.spinUrgency.setSingleStep(1)
        self.spinUrgency.setValue(5)
        
        gridleft = QGridLayout()
        gridleft.addWidget(labelSymbol, 0, 0)
        gridleft.addWidget(labelName, 1, 0)
        gridleft.addWidget(labelDirection, 2, 0)
        gridleft.addWidget(labelOffset, 3, 0)
        gridleft.addWidget(labelPrice, 4, 0)
        gridleft.addWidget(labelVolume, 5, 0)
        gridleft.addWidget(labelPriceType, 6, 0)
        gridleft.addWidget(labelUrgency, 7, 0)
        gridleft.addWidget(labelExchange, 8, 0)
        gridleft.addWidget(labelProductClass, 9, 0)
        gridleft.addWidget(labelCurrency, 10, 0)
        
        gridleft.addWidget(self.lineSymbol, 0, 1)
        gridleft.addWidget(self.lineName, 1, 1)
        gridleft.addWidget(self.comboDirection, 2, 1)
        
        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.comboOffset)
        lable1 = QLabel()
        hbox1.addWidget(lable1)
        hbox1.addWidget(self.tickOffset)
        hbox1.setStretchFactor(self.comboOffset, 4)
        hbox1.setStretchFactor(lable1, 1)
        hbox1.setStretchFactor(self.tickOffset, 3)
        gridleft.addItem(hbox1, 3, 1)
        
        gridleft.addWidget(self.spinPrice, 4, 1)
        gridleft.addWidget(self.spinVolume, 5, 1)
        gridleft.addWidget(self.comboPriceType, 6, 1)
        gridleft.addWidget(self.spinUrgency, 7, 1)
        gridleft.addWidget(self.comboExchange, 8, 1)
        gridleft.addWidget(self.comboProductClass, 9, 1)
        gridleft.addWidget(self.comboCurrency, 10, 1)
        
        # 右边部分
        labelBid1 = QLabel(u'买一')
        labelBid2 = QLabel(u'买二')
        labelBid3 = QLabel(u'买三')
        labelBid4 = QLabel(u'买四')
        labelBid5 = QLabel(u'买五')
        
        labelAsk1 = QLabel(u'卖一')
        labelAsk2 = QLabel(u'卖二')
        labelAsk3 = QLabel(u'卖三')
        labelAsk4 = QLabel(u'卖四')
        labelAsk5 = QLabel(u'卖五')
        
        self.labelBidPrice1 = QLabel()
        self.labelBidPrice2 = QLabel()
        self.labelBidPrice3 = QLabel()
        self.labelBidPrice4 = QLabel()
        self.labelBidPrice5 = QLabel()
        self.labelBidVolume1 = QLabel()
        self.labelBidVolume2 = QLabel()
        self.labelBidVolume3 = QLabel()
        self.labelBidVolume4 = QLabel()
        self.labelBidVolume5 = QLabel()
        
        self.labelAskPrice1 = QLabel()
        self.labelAskPrice2 = QLabel()
        self.labelAskPrice3 = QLabel()
        self.labelAskPrice4 = QLabel()
        self.labelAskPrice5 = QLabel()
        self.labelAskVolume1 = QLabel()
        self.labelAskVolume2 = QLabel()
        self.labelAskVolume3 = QLabel()
        self.labelAskVolume4 = QLabel()
        self.labelAskVolume5 = QLabel()
        
        labelLast = QLabel(u'最新')
        self.labelLastPrice = QLabel()
        self.labelReturn = QLabel()
        
        self.labelLastPrice.setMinimumWidth(60)
        self.labelReturn.setMinimumWidth(60)
        
        gridRight = QGridLayout()
        gridRight.addWidget(labelAsk5, 0, 0)
        gridRight.addWidget(labelAsk4, 1, 0)
        gridRight.addWidget(labelAsk3, 2, 0)
        gridRight.addWidget(labelAsk2, 3, 0)
        gridRight.addWidget(labelAsk1, 4, 0)
        gridRight.addWidget(labelLast, 5, 0)
        gridRight.addWidget(labelBid1, 6, 0)
        gridRight.addWidget(labelBid2, 7, 0)
        gridRight.addWidget(labelBid3, 8, 0)
        gridRight.addWidget(labelBid4, 9, 0)
        gridRight.addWidget(labelBid5, 10, 0)
        
        gridRight.addWidget(self.labelAskPrice5, 0, 1)
        gridRight.addWidget(self.labelAskPrice4, 1, 1)
        gridRight.addWidget(self.labelAskPrice3, 2, 1)
        gridRight.addWidget(self.labelAskPrice2, 3, 1)
        gridRight.addWidget(self.labelAskPrice1, 4, 1)
        gridRight.addWidget(self.labelLastPrice, 5, 1)
        gridRight.addWidget(self.labelBidPrice1, 6, 1)
        gridRight.addWidget(self.labelBidPrice2, 7, 1)
        gridRight.addWidget(self.labelBidPrice3, 8, 1)
        gridRight.addWidget(self.labelBidPrice4, 9, 1)
        gridRight.addWidget(self.labelBidPrice5, 10, 1)
        
        gridRight.addWidget(self.labelAskVolume5, 0, 2)
        gridRight.addWidget(self.labelAskVolume4, 1, 2)
        gridRight.addWidget(self.labelAskVolume3, 2, 2)
        gridRight.addWidget(self.labelAskVolume2, 3, 2)
        gridRight.addWidget(self.labelAskVolume1, 4, 2)
        gridRight.addWidget(self.labelReturn, 5, 2)
        gridRight.addWidget(self.labelBidVolume1, 6, 2)
        gridRight.addWidget(self.labelBidVolume2, 7, 2)
        gridRight.addWidget(self.labelBidVolume3, 8, 2)
        gridRight.addWidget(self.labelBidVolume4, 9, 2)
        gridRight.addWidget(self.labelBidVolume5, 10, 2)
        
        # 发单按钮
        buttonSendOrder = QPushButton(u'发单')
        buttonCancelAll = QPushButton(u'全撤')
        
        size = buttonSendOrder.sizeHint()
        buttonSendOrder.setMinimumHeight(size.height() * 2)  # 把按钮高度设为默认两倍
        buttonCancelAll.setMinimumHeight(size.height() * 2)
        
        # 整合布局
        hbox = QHBoxLayout()
        hbox.addLayout(gridleft)
        hbox.addLayout(gridRight)
        
        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(buttonSendOrder)
        vbox.addWidget(buttonCancelAll)
        vbox.addStretch()
        
        self.setLayout(vbox)
        
        # 关联更新
        buttonSendOrder.clicked.connect(self.sendOrder)
        buttonCancelAll.clicked.connect(self.cancelAll)
        self.lineSymbol.returnPressed.connect(self.updateSymbol)
        self.comboDirection.currentIndexChanged.connect(self.updateOffset)
        self.tickOffset.stateChanged.connect(self.updateOffset)
        
        self.labelAskPrice1.mouseDoubleClickEvent = self.ask1clicked
        self.labelAskPrice2.mouseDoubleClickEvent = self.ask2clicked
        self.labelAskPrice3.mouseDoubleClickEvent = self.ask3clicked
        self.labelAskPrice4.mouseDoubleClickEvent = self.ask4clicked
        self.labelAskPrice5.mouseDoubleClickEvent = self.ask5clicked
        
        self.labelBidPrice1.mouseDoubleClickEvent = self.bid1clicked
        self.labelBidPrice2.mouseDoubleClickEvent = self.bid2clicked
        self.labelBidPrice3.mouseDoubleClickEvent = self.bid3clicked
        self.labelBidPrice4.mouseDoubleClickEvent = self.bid4clicked
        self.labelBidPrice5.mouseDoubleClickEvent = self.bid5clicked
        
        self.labelLastPrice.mouseDoubleClickEvent = self.lastclicked
    
    def ask1clicked(self, a):
        self.askclicked(self.labelAskPrice1.text())
    
    def ask2clicked(self, a):
        self.askclicked(self.labelAskPrice2.text())
    
    def ask3clicked(self, a):
        self.askclicked(self.labelAskPrice3.text())
    
    def ask4clicked(self, a):
        self.askclicked(self.labelAskPrice4.text())
    
    def ask5clicked(self, a):
        self.askclicked(self.labelAskPrice5.text())
    
    def bid1clicked(self, a):
        self.bidclicked(self.labelBidPrice1.text())
    
    def bid2clicked(self, a):
        self.bidclicked(self.labelBidPrice2.text())
    
    def bid3clicked(self, a):
        self.bidclicked(self.labelBidPrice3.text())
    
    def bid4clicked(self, a):
        self.bidclicked(self.labelBidPrice4.text())
    
    def bid5clicked(self, a):
        self.bidclicked(self.labelBidPrice5.text())
    
    def lastclicked(self, a):
        self.setPrice(self.labelLastPrice.text())
    
    def setPrice(self, text):
        result = False
        if text is not None and len(text) > 0:
            price = float(str(text))
            if price > 0:
                self.spinPrice.setValue(price)
                result = True
        return result
    
    def askclicked(self, text):
        if self.setPrice(text):
            self.comboDirection.setCurrentIndex(self.directionList.index(DIRECTION_LONG))
            self.updateOffset()
    
    def bidclicked(self, text):
        if self.setPrice(text):
            self.comboDirection.setCurrentIndex(self.directionList.index(DIRECTION_SHORT))
            self.updateOffset()
    
    def updateOffset(self):
        if self.tickOffset.checkState():
            self.comboOffset.setEnabled(True)
            if self.comboProductClass.currentText() in (PRODUCT_EQUITY, PRODUCT_BOND):
                dir = self.comboDirection.currentText()
                if dir == DIRECTION_LONG:
                    self.comboOffset.setCurrentIndex(self.offsetList.index(OFFSET_OPEN) + 1)
                elif dir == DIRECTION_SHORT:
                    self.comboOffset.setCurrentIndex(self.offsetList.index(OFFSET_CLOSE) + 1)
            elif self.comboOffset.currentIndex() == 0:
                self.comboOffset.setCurrentIndex(1)
        else:
            self.comboOffset.setEnabled(False)
            self.comboOffset.setCurrentIndex(0)
    
    # ----------------------------------------------------------------------
    def updateSymbol(self):
        """合约变化"""
        # 读取组件数据
        symbol = str(self.lineSymbol.text())
        self.comboCurrency.setCurrentIndex(1)
        
        currency = safeUnicode(self.comboCurrency.currentText())
        gatewayName = safeUnicode('quantos')
        
        # 查询合约
        vtSymbol = symbol
        contract = self.mainEngine.getContract(symbol)
        
        # 清空价格数量
        self.spinPrice.setValue(0)
        self.spinVolume.setValue(0)
        
        if contract:
            vtSymbol = contract.vtSymbol
            gatewayName = contract.gatewayName
            self.lineName.setText(contract.name)
            p = self.lineName.palette()
            p.setColor(self.lineName.foregroundRole(), QtGui.QColor('black'))
            self.lineName.setPalette(p)
            exchange = contract.exchange
            productClass = contract.productClass
            self.comboExchange.setCurrentIndex(self.exchangeList.index(exchange))
            self.comboProductClass.setCurrentIndex(self.productClassList.index(productClass))
            self.spinPrice.setSingleStep(contract.priceTick)
            self.spinVolume.setSingleStep(contract.lotsize)
            
            self.updateOffset()
        
        else:
            self.comboExchange.setCurrentIndex(0)
            self.comboProductClass.setCurrentIndex(0)
            productClass = safeUnicode(self.comboProductClass.currentText())
            exchange = safeUnicode(self.comboExchange.currentText())
            self.lineName.setText(u'不存在')
            p = self.lineName.palette()
            p.setColor(self.lineName.foregroundRole(), QtGui.QColor('red'))
            self.lineName.setPalette(p)
        
        # 清空行情显示
        self.labelBidPrice1.setText('')
        self.labelBidPrice2.setText('')
        self.labelBidPrice3.setText('')
        self.labelBidPrice4.setText('')
        self.labelBidPrice5.setText('')
        self.labelBidVolume1.setText('')
        self.labelBidVolume2.setText('')
        self.labelBidVolume3.setText('')
        self.labelBidVolume4.setText('')
        self.labelBidVolume5.setText('')
        self.labelAskPrice1.setText('')
        self.labelAskPrice2.setText('')
        self.labelAskPrice3.setText('')
        self.labelAskPrice4.setText('')
        self.labelAskPrice5.setText('')
        self.labelAskVolume1.setText('')
        self.labelAskVolume2.setText('')
        self.labelAskVolume3.setText('')
        self.labelAskVolume4.setText('')
        self.labelAskVolume5.setText('')
        self.labelLastPrice.setText('')
        self.labelReturn.setText('')
        
        # 重新注册事件监听
        if self.signalemit != None:
            self.eventEngine.unregister(EVENT_TICK + self.symbol, self.signalemit)
        
        self.signalemit = self.signal.emit
        self.eventEngine.register(EVENT_TICK + vtSymbol, self.signalemit)
        
        # 订阅合约
        self.mainEngine.subscribe(contract.vtSymbol, gatewayName)
        
        # 更新组件当前交易的合约
        self.symbol = vtSymbol
    
    # ----------------------------------------------------------------------
    def updateTick(self, event):
        """更新行情"""
        tick = event.dict_['data']
        
        if tick.vtSymbol == self.symbol:
            self.labelBidPrice1.setText(str(tick.bidPrice1))
            self.labelAskPrice1.setText(str(tick.askPrice1))
            self.labelBidVolume1.setText(str(tick.bidVolume1))
            self.labelAskVolume1.setText(str(tick.askVolume1))
            
            if tick.bidPrice2:
                self.labelBidPrice2.setText(str(tick.bidPrice2))
                self.labelBidPrice3.setText(str(tick.bidPrice3))
                self.labelBidPrice4.setText(str(tick.bidPrice4))
                self.labelBidPrice5.setText(str(tick.bidPrice5))
                
                self.labelAskPrice2.setText(str(tick.askPrice2))
                self.labelAskPrice3.setText(str(tick.askPrice3))
                self.labelAskPrice4.setText(str(tick.askPrice4))
                self.labelAskPrice5.setText(str(tick.askPrice5))
                
                self.labelBidVolume2.setText(str(tick.bidVolume2))
                self.labelBidVolume3.setText(str(tick.bidVolume3))
                self.labelBidVolume4.setText(str(tick.bidVolume4))
                self.labelBidVolume5.setText(str(tick.bidVolume5))
                
                self.labelAskVolume2.setText(str(tick.askVolume2))
                self.labelAskVolume3.setText(str(tick.askVolume3))
                self.labelAskVolume4.setText(str(tick.askVolume4))
                self.labelAskVolume5.setText(str(tick.askVolume5))
            
            self.labelLastPrice.setText(str(tick.lastPrice))
            if self.spinPrice.value() < 0.000001 and tick.lastPrice > 0.000001:
                self.spinPrice.setValue(tick.lastPrice)
            
            if tick.preClosePrice:
                rt = (old_div(tick.lastPrice, tick.preClosePrice)) - 1
                self.labelReturn.setText(('%.2f' % (rt * 100)) + '%')
            else:
                self.labelReturn.setText('')
    
    # ----------------------------------------------------------------------
    def connectSignal(self):
        """连接Signal"""
        self.signal.connect(self.updateTick)
    
    # ----------------------------------------------------------------------
    def sendOrder(self):
        """发单"""
        symbol = str(self.lineSymbol.text()).strip()
        exchange = safeUnicode(self.comboExchange.currentText())
        price = self.spinPrice.value()
        volume = self.spinVolume.value()
        gatewayName = safeUnicode('quantos')
        
        if len(symbol) <= 0 or len(exchange) <= 0 or price <= 0 or volume <= 0:
            return
        
        # 查询合约
        if exchange:
            vtSymbol = '.'.join([symbol, exchange])
            contract = self.mainEngine.getContract(vtSymbol)
        else:
            vtSymbol = symbol
            contract = self.mainEngine.getContract(symbol)
        
        if contract:
            gatewayName = contract.gatewayName
            exchange = contract.exchange  # 保证有交易所代码
        
        req = VtOrderReq()
        req.symbol = symbol
        req.exchange = exchange
        req.price = price
        req.volume = volume
        req.direction = safeUnicode(self.comboDirection.currentText())
        req.priceType = safeUnicode(self.comboPriceType.currentText())
        req.offset = safeUnicode(self.comboOffset.currentText())
        req.urgency = self.spinUrgency.value()
        req.productClass = safeUnicode(self.comboProductClass.currentText())
        
        self.mainEngine.sendOrder(req, gatewayName)
    
    # ----------------------------------------------------------------------
    def cancelAll(self):
        """一键撤销所有委托"""
        l = self.mainEngine.getAllWorkingOrders()
        for order in l:
            req = VtCancelOrderReq()
            req.symbol = order.symbol
            req.exchange = order.exchange
            req.frontID = order.frontID
            req.sessionID = order.sessionID
            req.orderID = order.taskID
            self.mainEngine.cancelOrder(req, order.gatewayName)
    
    # ----------------------------------------------------------------------
    def closePosition(self, cell):
        """根据持仓信息自动填写交易组件"""
        # 读取持仓数据，cell是一个表格中的单元格对象
        pos = cell.data
        symbol = pos.symbol
        
        # 更新交易组件的显示合约
        self.lineSymbol.setText(symbol)
        self.updateSymbol()
        
        # 自动填写信息
        self.comboPriceType.setCurrentIndex(self.priceTypeList.index(PRICETYPE_LIMITPRICE))
        self.spinVolume.setValue(pos.enable)
        if pos.direction == DIRECTION_LONG or pos.direction == DIRECTION_NET:
            self.comboDirection.setCurrentIndex(self.directionList.index(DIRECTION_SHORT))
        else:
            self.comboDirection.setCurrentIndex(self.directionList.index(DIRECTION_LONG))
        
        if self.comboProductClass.currentText() not in (PRODUCT_EQUITY, PRODUCT_BOND):
            self.tickOffset.setChecked(True)
            self.comboOffset.setCurrentIndex(self.offsetList.index(OFFSET_CLOSE) + 1)
        elif self.tickOffset.checkState():
            self.comboOffset.setCurrentIndex(self.offsetList.index(OFFSET_CLOSE) + 1)
            
            # 价格留待更新后由用户输入，防止有误操作
    
    def fillSymbol(self, cell):
        
        tick = cell.data
        self.lineSymbol.setText(tick.symbol)
        
        self.updateSymbol()
        
        if type(cell) in (BidCell, AskCell):
            price = str(cell.text())
            if len(price) > 0:
                price = float(price)
                if price > 0:
                    self.spinPrice.setValue(price)
                    direction = DIRECTION_LONG if type(cell) is AskCell else DIRECTION_SHORT
                    self.comboDirection.setCurrentIndex(self.directionList.index(direction))
                    self.updateOffset()


########################################################################
class ContractMonitor(BasicMonitor):
    """合约查询"""
    
    # ----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine, parent=None):
        """Constructor"""
        super(ContractMonitor, self).__init__(parent=parent)
        
        self.mainEngine = mainEngine
        self.eventEngine = eventEngine
        
        d = OrderedDict()
        d['symbol'] = {'chinese': u'合约代码', 'cellType': BasicCell}
        d['exchange'] = {'chinese': u'交易所', 'cellType': BasicCell}
        d['vtSymbol'] = {'chinese': u'vt系统代码', 'cellType': BasicCell}
        d['name'] = {'chinese': u'名称', 'cellType': BasicCell}
        d['productClass'] = {'chinese': u'合约类型', 'cellType': BasicCell}
        d['size'] = {'chinese': u'合约乘数', 'cellType': BasicCell}
        d['lotsize'] = {'chinese': u'最小交易单位', 'cellType': BasicCell}
        d['priceTick'] = {'chinese': u'最小价格变动', 'cellType': BasicCell}
        self.setHeaderDict(d)
        
        self.initUi()
    
    # ----------------------------------------------------------------------
    def initUi(self):
        """初始化界面"""
        self.setWindowTitle(u'合约')
        self.setLineWidth(1)
        self.setFont(BASIC_FONT)
        self.initTable()
        
        # 设置数据键
        self.setDataKey('vtSymbol')
        
        self.setSorting(True)
        
        # 设置监控事件类型
        self.setEventType(EVENT_CONTRACT, EVENT_CONTRACT_CLEAR)
        
        self.initTable()
        self.registerEvent()
