# encoding: UTF-8

from builtins import str

from uiBasicWidget import QtGui

class LoginLine(QtGui.QFrame):
    """水平分割线"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        super(LoginLine, self).__init__()
        self.setFrameShape(self.HLine)
        self.setFrameShadow(self.Sunken)
        
########################################################################
class QuantOSLoginEngine(QtGui.QWidget):
    """风控引擎的管理组件"""

    #----------------------------------------------------------------------
    def __init__(self, gateway, setting, parent=None):
        """Constructor"""
        super(QuantOSLoginEngine, self).__init__(parent)
        
        self.setting = setting
        self.gateway = gateway
        self.connectionMap = {}
        
        self.initUi()

    #----------------------------------------------------------------------
    def initUi(self):
        """初始化界面"""
        self.setWindowTitle(u'登录')
        
        # 设置界面
        self.userName = QtGui.QLineEdit()
        self.password = QtGui.QTextEdit()
        self.comboStrategy = QtGui.QComboBox()
        
        grid = QtGui.QGridLayout()
        grid.addWidget(LoginLine(), 1, 0, 1, 2)
        grid.addWidget(QtGui.QLabel(u'用户名'), 2, 0)
        grid.addWidget(self.userName, 2, 1)
        grid.addWidget(QtGui.QLabel(u'令牌'), 3, 0)
        grid.addWidget(self.password, 3, 1)
        grid.addWidget(LoginLine(), 4, 0, 1, 2)
        grid.addWidget(QtGui.QLabel(u'策略'), 5, 0)
        grid.addWidget(self.comboStrategy, 5, 1)
        grid.addWidget(LoginLine(), 6, 0, 1, 2)
     
        self.buttonCancel = QtGui.QPushButton(u'取消')
        self.buttonConfirm = QtGui.QPushButton(u'确认')
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.buttonConfirm)
        hbox.addWidget(self.buttonCancel)
        self.buttonConfirm.setDefault(True)

        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(grid)
        vbox.addLayout(hbox)
        self.setLayout(vbox)
        
        # 设为固定大小
        self.setFixedSize(self.sizeHint())
        
        self.buttonCancel.clicked.connect(self.close)
        self.buttonConfirm.clicked.connect(self.login)
        self.userName.returnPressed.connect(self.password.setFocus)
        
        # init username & token
        username = self.setting['username']
        token    = self.setting['token']
        
        self.userName.setText(username)
        self.password.setText(token)
        
    def login(self):
        selectedStrat = self.comboStrategy.currentText()
        if selectedStrat is not None and len(selectedStrat) > 0:
            username = str(self.userName.text()).strip()
            password = str(self.password.toPlainText()).strip()
            if len(username) <= 0 or len(password) <= 0:
                QtGui.QMessageBox.warning(self, u'登录', u'输入用户名和密码')
            else:
                self.close()
                self.gateway.login(username, password, selectedStrat)
        else:
            self.connect()
        
    def connect(self):
        userName = str(self.userName.text()).strip()
        password = str(self.password.toPlainText()).strip()
        if len(userName) <= 0 or len(password) <= 0:
            QtGui.QMessageBox.warning(self, u'获取策略', u'输入用户名和密码')
        else:
            strategyList = self.gateway.getStrategyList(userName, password)
            if strategyList is not None and len(strategyList) > 0:
                self.comboStrategy.clear()
                strategyList_sl = []
                for strategy in strategyList:
                    strategyList_sl.append(str(strategy))
                strategyList_sl.sort()
                self.comboStrategy.addItems(strategyList_sl)
                self.userName.setEnabled(False)
                self.password.setEnabled(False)

            else:
                QtGui.QMessageBox.warning(self, u'获取策略', u'无法获取相关策略')
                self.comboStrategy.clear()
            
            self.comboStrategy.setFocus()
              
    