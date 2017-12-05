# encoding: UTF-8

import sys
import os
import ctypes
import platform

from imp import reload 
            
from vtEngine import MainEngine
from uiMainWindow import *


#----------------------------------------------------------------------
def main():
    """主程序入口"""
    # 重载sys模块，设置默认字符串编码方式为utf8
    reload(sys)
    try:
        sys.setdefaultencoding('utf8')
    except:
        pass
    
    # 设置Windows底部任务栏图标
    if 'Windows' in platform.uname() :
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('vn.trader')  

    # 初始化Qt应用对象
    icon = os.path.join(os.getcwd(), 'setting', 'vnpy.ico')
    
    app = QtGui.QApplication(['VnTrader',''])
    app.setWindowIcon(QtGui.QIcon(icon))
    app.setFont(BASIC_FONT)
    
    darksheet = qdarkstyle.load_stylesheet(pyside=False)
    whitesheet = app.styleSheet()
    sheets = [whitesheet, darksheet]
    # 设置Qt的皮肤
    try:
        f = file("setting/VT_setting.json")
        setting = json.load(f)
        if setting['darkStyle']:
            app.setStyleSheet(darksheet)
            sheets = [darksheet, whitesheet]
    except:
        pass
    
    # 初始化主引擎和主窗口对象
    mainEngine = MainEngine()
    mainWindow = MainWindow(mainEngine, mainEngine.eventEngine, app, sheets)
    mainWindow.showMaximized()
    mainWindow.showLogin()
    
    # 在主线程中启动Qt事件循环
    sys.exit(app.exec_())
    
if __name__ == '__main__':
    main()
