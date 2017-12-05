## vnTrader使用帮助

0. 软件下载。

+ 请从[这里](https://github.com/quantOS-org/TradeSim/tree/master/vnTrader)下载
+ 软件运行需要依赖pyqt4，请从[这个网页](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyqt4)下载相应的版本，并安装。`pip install xxx.whl`

1. 请在vnTrader程序目录，通过如下命令启动vnTrader:
```shell
python vtMain.py
```
在windows上，可以直接点击start.bat运行，如下图所示:

![](https://github.com/quantOS-org/TradeSim/blob/master/doc/img/vnTrader_start.png)

2. 系统提示登录，在登录框输入手机号和token，如下图

![](https://github.com/quantOS-org/TradeSim/blob/master/doc/img/vnTrader_login.png)

**此时的策略号无法选择**，直接点击确定，系统会加载出策略号，如下图

![](https://github.com/quantOS-org/TradeSim/blob/master/doc/img/vnTrader_strategy.png)

选择你要操作的策略号，再次点击确定，进入系统主界面，如下图：

![](https://github.com/quantOS-org/TradeSim/blob/master/doc/img/vnTrader_main.png)

主界面主要包括：交易，行情，持仓，委托，成交，资金，日志，合约等几个大的面板，用于展示用户的详细交易信息。

3. 发起委托

在交易界面，用户可以输入需要交易的标的代码、价格、数量，选择适当的算法，点击发单，即可进行委托。如下图

![](https://github.com/quantOS-org/TradeSim/blob/master/doc/img/vnTrader_order.png)

4. 发起撤单

有两种方式可以撤单：

（1）点击交易模块的“全撤”按钮。

（2）双击委托模块的指定委托记录。

![](https://github.com/quantOS-org/TradeSim/blob/master/doc/img/vnTrader_cancel.png)

