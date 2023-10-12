import backtrader as bt
import pandas as pd
import datetime
import matplotlib.pyplot as plt

class TurtleTradingStrategy(bt.Strategy):
    params = dict(
        N1=20,  # 唐奇安通道上轨的t
        N2=10,  # 唐奇安通道下轨的t
    )

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.order = None
        self.buy_count = 0  # 记录买入次数
        self.last_price = 0  # 记录买入价格
        # 准备第一个标的沪深300主力合约的close、high、low 行情数据

        # self.close = self.datas[0].close
        self.open_line = self.datas[0].open
        self.close_line = self.datas[0].close
        self.high = self.datas[0].high
        self.low = self.datas[0].low
        self.openinterest = self.datas[0].openinterest
        # # 计算唐奇安通道上轨：过去20日的最高价
        # self.DonchianH = bt.ind.Highest(self.high(-1), period=self.p.N1, subplot=True)
        # # 计算唐奇安通道下轨：过去10日的最低价
        # self.DonchianL = bt.ind.Lowest(self.low(-1), period=self.p.N2, subplot=True)
        # # 生成唐奇安通道上轨突破：close>DonchianH，取值为1.0；反之为 -1.0
        # self.CrossoverH = bt.ind.CrossOver(self.close(0), self.DonchianH, subplot=False)
        # # 生成唐奇安通道下轨突破:
        # self.CrossoverL = bt.ind.CrossOver(self.close(0), self.DonchianL, subplot=False)
        # # 计算 ATR
        # self.TR = bt.ind.Max((self.high(0) - self.low(0)),  # 当日最高价-当日最低价
        #                      abs(self.high(0) - self.close(-1)),  # abs(当日最高价−前一日收盘价)
        #                      abs(self.low(0) - self.close(-1)))  # abs(当日最低价-前一日收盘价)
        # self.ATR = bt.ind.SimpleMovingAverage(self.TR, period=self.p.N1, subplot=False)
        # # 计算 ATR，直接调用 talib ，使用前需要安装 python3 -m pip install TA-Lib
        # self.ATR = bt.talib.ATR(self.high, self.low, self.datas[0].close, timeperiod=self.p.N1, subplot=True)

    def next(self):
        print(bt.num2date(self.data.datetime[0]).isoformat())
        print('getcash 当前可用资金', self.broker.getcash())
        print('getvalue 当前总资产', self.broker.getvalue())
        print(bt.num2date(self.data.datetime[-1]).isoformat())
        print('self.stats 当前可用资金', self.stats.broker.cash[0])
        print('self.stats 当前总资产', self.stats.broker.value[0])
        print('self.stats 最大回撤', self.stats.drawdown.drawdown[0])
        print('self.stats 收益', self.stats.timereturn.line[0])
        # 如果还有订单在执行中，就不做新的仓位调整
        if self.order:
            return

            # 如果当前持有多单
        if self.position.size > 0:
            print('self.position.size:{} close:{}'.format(self.position.size, ' buy'))
            self.order = self.close()
            self.buy_count = 0

                # 如果当前持有空单
        elif self.position.size < 0:
            print('self.position.size:{} close:{}'.format(self.position.size, ' sell'))
            self.order = self.close()
            self.buy_count = 0


        else:  # 如果没有持仓，等待入场时机
            # 入场: 价格突破上轨线且空仓时，做多
            if self.openinterest[0] < 3 and self.buy_count == 0:
                # 计算建仓单位：self.ATR*期货合约乘数300*保证金比例0.1
                # self.buy_unit = max((self.broker.getvalue() * 0.005) / (self.ATR * 300 * 0.1), 1)
                self.buy_unit = 1  # 交易单位为手
                self.order = self.buy(size=self.buy_unit)
                self.last_price = self.position.price  # 记录买入价格
                self.buy_count = 1  # 记录本次交易价格
                print('self.openinterest:{} < 2 buy close:{}, open:{}, price:{}, order:{}'.format(self.openinterest[0],self.close_line[0], self.open_line[0], self.last_price, self.order))

            # 入场: 价格跌破下轨线且空仓时，做空
            elif self.openinterest[0] > 3 and self.buy_count == 0:
                self.buy_unit = 1  # 交易单位为手
                self.order = self.sell(size=self.buy_unit)
                self.last_price = self.position.price  # 记录买入价格
                self.buy_count = 1  # 记录本次交易价格
                print('self.openinterest:{} > 2 sell close:{}, open:{}, price:{}, order:{}'.format(self.openinterest[0],
                                                                                                  self.close_line[0],
                                                                                                  self.open_line[0],
                                                                                                  self.last_price,
                                                                                                  self.order))

    # 打印订单日志
    def notify_order(self, order):
        order_status = ['Created', 'Submitted', 'Accepted', 'Partial',
                        'Completed', 'Canceled', 'Expired', 'Margin', 'Rejected']
        # 未被处理的订单
        if order.status in [order.Submitted, order.Accepted]:
            self.log('ref:%.0f, name: %s, Order: %s' % (order.ref,
                                                        order.data._name,
                                                        order_status[order.status]))
            return
        # 已经处理的订单
        if order.status in [order.Partial, order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, status: %s, ref:%.0f, name: %s, Size: %.2f, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order_status[order.status],  # 订单状态
                     order.ref,  # 订单编号
                     order.data._name,  # 股票名称
                     order.executed.size,  # 成交量
                     order.executed.price,  # 成交价
                     order.executed.value,  # 成交额
                     order.executed.comm))  # 佣金
            else:  # Sell
                self.log(
                    'SELL EXECUTED, status: %s, ref:%.0f, name: %s, Size: %.2f, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order_status[order.status],
                     order.ref,
                     order.data._name,
                     order.executed.size,
                     order.executed.price,
                     order.executed.value,
                     order.executed.comm))

        elif order.status in [order.Canceled, order.Margin, order.Rejected, order.Expired]:
            # 订单未完成
            self.log('ref:%.0f, name: %s, status: %s' % (
                order.ref, order.data._name, order_status[order.status]))

        self.order = None

    def notify_trade(self, trade):
        # 交易刚打开时
        if trade.justopened:
            self.log('Trade Opened, name: %s, Size: %.2f,Price: %.2f' % (
                trade.getdataname(), trade.size, trade.price))
        # 交易结束
        elif trade.isclosed:
            self.log('Trade Closed, name: %s, GROSS %.2f, NET %.2f, Comm %.2f' % (
                trade.getdataname(), trade.pnl, trade.pnlcomm, trade.commission))
        # 更新交易状态
        else:
            self.log('Trade Updated, name: %s, Size: %.2f,Price: %.2f' % (
                trade.getdataname(), trade.size, trade.price))

    def stop(self):
        print('---------stop----------')
        print(bt.num2date(self.data.datetime[0]).isoformat())
        print('getcash 当前可用资金', self.broker.getcash())
        print('getvalue 当前总资产', self.broker.getvalue())
        print(bt.num2date(self.data.datetime[-1]).isoformat())
        print('self.stats 当前可用资金', self.stats.broker.cash[0])
        print('self.stats 当前总资产', self.stats.broker.value[0])
        print('self.stats 最大回撤', self.stats.drawdown.drawdown[0])
        print('self.stats 收益', self.stats.timereturn.line[0])

# 创建主控制器
cerebro = bt.Cerebro()
# 准备股票日线数据，输入到backtrader
IF_price = pd.read_csv('../data/IF02022_2023.csv', parse_dates=['datetime'], index_col=0)
datafeed = bt.feeds.PandasData(dataname=IF_price,
                               fromdate=pd.to_datetime('2022-01-01'),
                               todate=pd.to_datetime('2023-09-30'))
print(datafeed)
cerebro.adddata(datafeed, name='IF')
# 初始资金 100,000,000
cerebro.broker.setcash(200000.0)
cerebro.broker.setcommission(commission=0.1,  # 按 0.1% 来收取手续费
                             mult=300,  # 合约乘数
                             margin=0.1,  # 保证金比例
                             percabs=False,  # 表示 commission 以 % 为单位
                             commtype=bt.CommInfoBase.COMM_FIXED,
                             stocklike=False)

# 加入策略
cerebro.addstrategy(TurtleTradingStrategy)
# 回测时需要添加 python -m pip install --upgrade pipPyFolio 分析器
cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')


cerebro.addanalyzer(bt.analyzers.TimeDrawDown, _name='_TimeDrawDown')
cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='_TimeReturn')
cerebro.addobserver(bt.observers.DrawDown)
cerebro.addobserver(bt.observers.TimeReturn)
cerebro.addobserver(bt.observers.Benchmark, data=datafeed)

result = cerebro.run()

cerebro.plot(iplot=False)

# 借助 pyfolio 进一步做回测结果分析

pyfolio = result[0].analyzers.pyfolio  # 注意：后面不要调用 .get_analysis() 方法
# 或者是 result[0].analyzers.getbyname('pyfolio')
returns, positions, transactions, gross_lev = pyfolio.get_pf_items()

# import pyfolio as pf
#
# pf.create_full_tear_sheet(returns)