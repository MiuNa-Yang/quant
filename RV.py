import math
import numpy as np
import quantstats
import talib
import backtrader as bt
import pandas as pd
import backtrader.analyzers as btanalyzers
import math

import backtrader as bt
import backtrader.analyzers as btanalyzers
import numpy as np
import pandas as pd
import quantstats
import talib


class RVI(bt.Indicator):
    lines = ('std', 'pos', 'neg', 'rvi')

    plotlines = dict(
        std=dict(_plotskip=True),
        pos=dict(_plotskip=True),
        neg=dict(_plotskip=True),
        rvi=dict(_plotskip=False)
    )

    params = (
        ('period', 20),
    )

    def __init__(self):
        self.lines.std = talib.STDDEV(self.datas[0].close, timeperiod=10, nbdev=2.0)

    def next(self):
        if self.lines.std[0] > self.lines.std[-1]:
            self.lines.pos[0] = self.lines.std[0]
        else:
            self.lines.pos[0] = 0

        if self.lines.std[0] < self.lines.std[-1]:
            self.lines.neg[0] = self.lines.std[0]
        else:
            self.lines.neg[0] = 0

        pos_nan = np.nan_to_num(self.lines.pos.get(size=self.params.period))
        neg_nan = np.nan_to_num(self.lines.neg.get(size=self.params.period))

        Usum = math.fsum(pos_nan)
        Dsum = math.fsum(neg_nan)

        if (Usum + Dsum) == 0:
            self.lines.rvi[0]=0
            return

        self.lines.rvi[0] = 100 * Usum / (Usum+Dsum)


class Strategy(bt.Strategy):
    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.rvi = RVI()
        #self.close = self.data.close


    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: {:.2f}, Cost: {:.2f}, Comm {:.2f}'.format(
                        order.executed.price,
                        order.executed.value,
                        order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: {:.2f}, Cost: {:.2f}, Comm {:.2f}'.format(
                    order.executed.price,
                    order.executed.value,
                    order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))


    def next(self):
        up = 60
        down = 35
        size_1 = math.floor(cerebro.broker.get_cash() * 0.90 / self.datas[0].close[0])
        if not self.position:
            if self.rvi.rvi[0] > up:
                if self.rvi.rvi[-1] < up and self.rvi.rvi[-2] < up:
                    self.order = self.buy(size=size_1, exectype=bt.Order.StopTrail, trailpercent=0.11)
        else:
            if self.rvi.rvi[0] < down:
                if self.rvi.rvi[-1] > down and self.rvi.rvi[-2] > down:
                    self.order = self.sell()


if __name__ == '__main__':



    stock = '601216.SH'
    start_date = '20100701'
    end_date = '20210109'

    df = pd.read_csv('data/000063.XSHE.csv')
    df.index = pd.to_datetime(df.date)
    df['openinterest'] = 0
    df = df[['open', 'close', 'high', 'low', 'volume', 'openinterest']]

    data = bt.feeds.PandasData(dataname=df)

    cerebro = bt.Cerebro()
    cerebro.adddata(data)

    cerebro.addstrategy(Strategy)
    cerebro.broker.setcash(1000000)
    cerebro.broker.setcommission(commission=0)
    cerebro.addsizer(bt.sizers.PercentSizer, percents=100)

    cerebro.addanalyzer(btanalyzers.SharpeRatio, _name = 'sharpe')
    cerebro.addanalyzer(btanalyzers.DrawDown, _name = 'drawdown')
    cerebro.addanalyzer(btanalyzers.Returns, _name='returns')
    cerebro.addanalyzer(btanalyzers.SQN, _name='sqn')
    cerebro.addanalyzer(bt.analyzers.PyFolio, _name='PyFolio')


    print(f'Starte Portfolio Value {cerebro.broker.getvalue()}')
    result = cerebro.run()

    print('----------------------------')
    print(f'End portfolio value {cerebro.broker.getvalue()}')
    print('----------------------------')
    print(f"Total Return:  {round(result[0].analyzers.returns.get_analysis()['rtot']*100, 2)}%")
    print(f"APR:           {round(result[0].analyzers.returns.get_analysis()['rnorm100'],2)}%")
    print(f"Max DrawDown:  {round(result[0].analyzers.drawdown.get_analysis()['max']['drawdown'],2)}%")
    print(f"Sharpe Ratio:  {round(result[0].analyzers.sharpe.get_analysis()['sharperatio'],2)}")
    #print(f"SQN:           {round(result[0].analyzers.sqn.get_analysis()['sqn'],2)}")
    portfolio_stats = result[0].analyzers.getbyname('PyFolio')
    returns, positions, transactions, gross_lev = portfolio_stats.get_pf_items()
    returns.index = returns.index.tz_convert(None)
    quantstats.reports.html(returns, output=f'results/{stock} Result_3.html', title=f'{stock} Analysis')