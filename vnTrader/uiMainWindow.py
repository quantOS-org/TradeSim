# encoding: UTF-8

from builtins import str

import psutil

# import sys
# PyQt 4/5 compatibility
try:
    from PyQt4.QtGui import QMainWindow, QDialog, QDockWidget, QAction, QHeaderView, QMessageBox, QLabel, QVBoxLayout
    from PyQt4 import QtCore
except ImportError:
    from PyQt5.QtWidgets import QMainWindow, QDialog, QDockWidget, QAction, QHeaderView, QMessageBox, QLabel, QVBoxLayout
    from PyQt5 import QtCore

from uiBasicWidget import *

import uiBasicWidget as wgs
#from . import uiBasicWidget as wgs

########################################################################
class MainWindow(QMainWindow):
    """主窗口"""
    signalStatusBar = QtCore.pyqtSignal(type(Event()))
    
    # ----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine, app, sheets):
        """Constructor"""
        super(MainWindow, self).__init__()
        
        self.mainEngine = mainEngine
        self.eventEngine = eventEngine
        self.app = app
        self.sheets = sheets
        
        self.widgetDict = {}  # 用来保存子窗口的字典
        
        self.initUi()
        self.eventEngine.register(EVENT_TITLE, self.updateTitle)
        
        self.sid = None
    
    def updateTitle(self, event):
        (user, stratid) = event.dict_['data']
        #self.setWindowTitle('VnTrader: ' + str(user) + "/" + str(stratid))
        self.sid = stratid
    
    # ----------------------------------------------------------------------
    def initUi(self):
        """初始化界面"""
        self.setWindowTitle('VnTrader')
        self.initCentral()
        self.initMenu()
        # self.initStatusBar()
    
    def showLogin(self):
        self.connectQuantOS()
    
    # ----------------------------------------------------------------------
    def initCentral(self):
        
        """初始化中心区域"""
        widgetTradingW, dockTradingW = self.createDock(wgs.TradingWidget, u'交易', QtCore.Qt.LeftDockWidgetArea)
        
        widgetMarketM, dockMarketM = self.createDock(wgs.MarketMonitor, u'行情', QtCore.Qt.RightDockWidgetArea)
        widgetPositionM, dockPositionM = self.createDock(wgs.PositionMonitor, u'持仓', QtCore.Qt.RightDockWidgetArea)
        
        widgetAccountM, dockAccountM = self.createDock(wgs.AccountMonitor, u'资金', QtCore.Qt.BottomDockWidgetArea)
        widgetContractM, dockContractM = self.createDock(wgs.ContractMonitor, u'合约', QtCore.Qt.BottomDockWidgetArea)
        widgetLogM, dockLogM = self.createDock(wgs.LogMonitor, u'日志', QtCore.Qt.BottomDockWidgetArea)
        
        widgetTradeM, dockTradeM = self.createDock(wgs.TradeMonitor, u'成交', QtCore.Qt.BottomDockWidgetArea)
        widgetOrderM, dockOrderM = self.createDock(wgs.OrderMonitor, u'委托', QtCore.Qt.BottomDockWidgetArea)
        
        self.tabifyDockWidget(dockContractM, dockTradeM)
        self.tabifyDockWidget(dockTradeM, dockOrderM)
        self.tabifyDockWidget(dockAccountM, dockLogM)
        
        dockOrderM.raise_()
        dockLogM.raise_()
        
        # 连接组件之间的信号
        widgetPositionM.itemDoubleClicked.connect(widgetTradingW.closePosition)
        widgetMarketM.itemDoubleClicked.connect(widgetTradingW.fillSymbol)
    
    # ----------------------------------------------------------------------
    def initMenu(self):
        """初始化菜单"""
        # 创建操作
        connectQuantOSAction = QAction(u'连接和切换策略', self)
        connectQuantOSAction.triggered.connect(self.connectQuantOS)
        
        exitAction = QAction(u'退出', self)
        exitAction.triggered.connect(self.close)
        
        aboutAction = QAction(u'关于', self)
        aboutAction.triggered.connect(self.openAbout)
        
        colorAction = QAction(u'变色', self)
        colorAction.triggered.connect(self.changeColor)
        
        # 创建菜单
        menubar = self.menuBar()
        
        # 设计为只显示存在的接口
        sysMenu = menubar.addMenu(u'系统')
        if 'quantos' in self.mainEngine.gatewayDict:
            sysMenu.addAction(connectQuantOSAction)
        sysMenu.addSeparator()
        sysMenu.addAction(exitAction)
        
        # 帮助
        helpMenu = menubar.addMenu(u'帮助')
        helpMenu.addAction(aboutAction)
        helpMenu.addAction(colorAction)
    
    # ----------------------------------------------------------------------
    def initStatusBar(self):
        """初始化状态栏"""
        self.statusLabel = QLabel()
        self.statusLabel.setAlignment(QtCore.Qt.AlignLeft)
        
        self.statusBar().addPermanentWidget(self.statusLabel)
        self.statusLabel.setText(self.getCpuMemory())
        
        self.sbCount = 0
        self.sbTrigger = 10  # 10秒刷新一次
        self.signalStatusBar.connect(self.updateStatusBar)
        self.eventEngine.register(EVENT_TIMER, self.signalStatusBar.emit)
    
    # ----------------------------------------------------------------------
    def updateStatusBar(self, event):
        """在状态栏更新CPU和内存信息"""
        self.sbCount += 1
        
        if self.sbCount == self.sbTrigger:
            self.sbCount = 0
            self.statusLabel.setText(self.getCpuMemory())
    
    # ----------------------------------------------------------------------
    def getCpuMemory(self):
        """获取CPU和内存状态信息"""
        cpuPercent = psutil.cpu_percent()
        memoryPercent = psutil.virtual_memory().percent
        return u'CPU使用率：%d%%   内存使用率：%d%%' % (cpuPercent, memoryPercent)
        
        # ----------------------------------------------------------------------
    
    def connectQuantOS(self):
        self.mainEngine.connect('quantos')
        
        # ----------------------------------------------------------------------
    
    def openAbout(self):
        """打开关于"""
        try:
            self.widgetDict['aboutW'].show()
        except KeyError:
            self.widgetDict['aboutW'] = AboutWidget(self)
            self.widgetDict['aboutW'].show()
    
    # ----------------------------------------------------------------------
    def closeEvent(self, event):
        """关闭事件"""
        reply = QMessageBox.question(self, u'退出',
                                     u'确认退出?', QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            for widget in list(self.widgetDict.values()):
                widget.close()
            
            self.mainEngine.exit()
            event.accept()
        else:
            event.ignore()
    
    # ----------------------------------------------------------------------
    def createDock(self, widgetClass, widgetName, widgetArea):
        """创建停靠组件"""
        widget = widgetClass(self.mainEngine, self.eventEngine)
        dock = QDockWidget(widgetName)
        dock.setWidget(widget)
        dock.setObjectName(widgetName)
        dock.setFeatures(dock.DockWidgetFloatable | dock.DockWidgetMovable)
        self.addDockWidget(widgetArea, dock)
        return widget, dock
    
    def changeColor(self):
        self.app.setStyleSheet(self.sheets[1])
        self.sheets = [self.sheets[1], self.sheets[0]]


########################################################################
class AboutWidget(QDialog):
    """显示关于信息"""
    
    # ----------------------------------------------------------------------
    def __init__(self, parent=None):
        """Constructor"""
        super(AboutWidget, self).__init__(parent)
        
        self.initUi()
    
    # ----------------------------------------------------------------------
    def initUi(self):
        """"""
        self.setWindowTitle(u'关于VnTrader')
        
        text = u"""
            quantos trade client
            """
        
        label = QLabel()
        label.setText(text)
        label.setMinimumWidth(500)
        
        vbox = QVBoxLayout()
        vbox.addWidget(label)
        
        self.setLayout(vbox)
