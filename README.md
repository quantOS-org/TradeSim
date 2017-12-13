## 项目简介 
TradeSim是一个在线仿真交易平台（未开源），提供账户管理、在线交易、模拟成交等服务，支持股票、期货等品种的交易。
TradeSim中的交易系统模块支持多账户管理、多通道交易、实时风控，提供包括VWAP、TWAP、配对交易、篮子下单在内的算法交易，是一款企业级应用。

![](https://github.com/quantOS-org/TradeSim/blob/master/doc/img/tradesim.png)

## 功能特色 

- 通过TradeAPI进行程序化下单。
- 支持股票、ETF、股指期货、国债期货、商品期货等品种的交易业务。
- 支持VWAP、TWAP等算法交易下单。
- 支持根据实时行情进行模拟撮合。
- 永久保存用户的历史交易、持仓信息。
- 支持对历史交易进行PNL分析、绩效归因、数据查询。
- VN.PY已实现与TradeSim的集成，用户可以通过VN.PY界面进行模拟交易。

## 客户端使用

TradeSim提供Web客户端、专用Python客户端等访问方式。支持Python 2.7/3.6，支持PyQt 4/5.

1. Web客户端：请登录[仿真交易](http://www.quantos.org/tradesim/trade.html)后使用。使用帮助参见[https://github.com/quantOS-org/TradeSim/tree/master/doc/webClient.md](https://github.com/quantOS-org/TradeSim/tree/master/doc/webClient.md)
2. 专用Python客户端：提供vnTrader客户端，请从[这里](https://github.com/quantOS-org/TradeSim/tree/master/vnTrader)下载。使用帮助参见[https://github.com/quantOS-org/TradeSim/tree/master/doc/vnTrader.md](https://github.com/quantOS-org/TradeSim/tree/master/doc/vnTrader.md)

## 交易API使用说明

请参见[TradeApi说明文档](https://github.com/quantOS-org/TradeAPI)。
