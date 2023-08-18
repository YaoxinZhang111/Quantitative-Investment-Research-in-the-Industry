import backtrader as bt
import pandas as pd
import datetime 
from stockstats import StockDataFrame as sdf
from config import ALL_FEATURES,INDICATORS,STOCK_LIST
# STOCK_LIST.remove('.DS_Store')
import chart_studio.plotly as py
import plotly.graph_objs as go
from plotly.offline import iplot

def add_technical_indicator(data):
        # 增加技术指标
        temp_indictor = data
        indicator_data = sdf.retype(data)
        for i in INDICATORS:
            temp_indictor = indicator_data[i]
            indicator_data[i] = temp_indictor
        return indicator_data


def get_history_data(stocks,begin_date,end_date,indicatas):
    global datas
    dts = pd.DataFrame()
    indicatas.append('datetime')
    indicatas.append('code')
    for stock in stocks:
        if len(datas[(datas.code == stock) & (datas.close == 0)]) > 0:
            continue
        dt = datas[(datas.code==stock) & (datas['datetime']>=pd.Timestamp(begin_date+datetime.timedelta(days=-1))) & (datas['datetime'] < pd.Timestamp(end_date))]
        dts = pd.concat([dts,dt])
    dts = dts.loc[:,indicatas]
    return dts

# 实例化 cerebro
cerebro = bt.Cerebro()
cash = 100000000
profit = pd.read_csv('./log/profit.csv')
deficit = pd.read_csv('./log/deficit.csv')

trade_info = pd.concat([profit,deficit])


ground_data = pd.read_csv('./data/inital_data/sh.000001.csv')
ground_date = pd.DataFrame(ground_data['date'].unique(), columns=['date'])

# 按股票代码，依次循环传入数据
datas = pd.DataFrame()
for stock in STOCK_LIST:
    try:
        # 日期对齐
        read_path = './data/inital_data/%s' % stock
        df = pd.read_csv(read_path)
        data_ = pd.merge(ground_date, df, how='left', on='date')
        data_.rename(columns={'date':'datetime'},inplace=True)
        data_.datetime = pd.to_datetime(data_.datetime)
        # data_ = data_.set_index("datetime")
        # 缺失值处理：日期对齐时会使得有些交易日的数据为空，所以需要对缺失数据进行填充
        data_.loc[:, ['volume',]] = data_.loc[:, ['volume',]].fillna(0)
        data_.loc[:, ['open', 'high', 'low', 'close']] = data_.loc[:, ['open', 'high', 'low', 'close']].fillna(method='pad')
        data_.loc[:, ['open', 'high', 'low', 'close']] = data_.loc[:, ['open', 'high', 'low', 'close']].fillna(0)
        data_['code'] = stock
        # 导入数据
        datafeed = bt.feeds.PandasData(dataname=data_, fromdate=datetime.datetime(2009, 1, 5),
                                    todate=datetime.datetime(2022, 7, 1))
        cerebro.adddata(datafeed, name=stock)  # 通过 name 实现数据集与股票的一一对应
        indicator_data = add_technical_indicator(data_)
        datas = pd.concat([datas,indicator_data])
        print(f"{stock} Done !")
    except:pass

print("All stock Done !")



# 回测策略
class TestStrategy(bt.Strategy):
    '''选股策略'''
    params = (('maperiod', 15),
              ('printlog', False),)
    
    def __init__(self):
        self.buy_stock = trade_info  # 保留调仓列表
        # 读取调仓日期，回测时，会在这一天下单，然后在下一个交易日，以开盘价买入
        self.buy_dates = pd.to_datetime(self.buy_stock['buy_date'].unique()).tolist()
        self.sell_datas = pd.to_datetime(self.buy_stock['sell_date'].unique()).tolist()
        self.order_list = []  # 记录以往订单，方便调仓日对未完成订单做处理
        self.buy_stocks_pre = []  # 记录上一期持仓
        self.base_initial = self.getdatabyname('sh.000001.csv').lines.close[1]
        self.call = []
    def next(self):
        hold_stock = [_p._name for _p in self.broker.positions if self.broker.getposition(_p).size > 0]
        values = (self.stats.broker.value[0]/cash)-1
        base_value = (self.getdatabyname('sh.000001.csv').lines.close[-1]/self.base_initial)-1
        dt = self.datas[0].datetime.date(0)  # 获取当前的回测时间点
        self.call.append([dt,values,base_value])
        # 如果是调仓日，则进行调仓操作
        
        
        history = get_history_data(stocks=STOCK_LIST,begin_date=dt,end_date=dt,indicatas=['close_5_sma','close_60_sma'])
        print(history)
        buy_stocks = history[(history.close_5_sma-history.close_60_sma > 0) & (history.close_5_sma-history.close_60_sma < 1)]
        buy_stocks = buy_stocks['code'].tolist()
        long_list = []
        for i in buy_stocks:
            if i not in hold_stock:
                long_list.append(i)
    
        sell_stock = history[(history.close_5_sma-history.close_60_sma <0)]
        sell_stock = sell_stock['code'].tolist()
        sell_list = []
        for i in sell_stock:
            if i in hold_stock:
                sell_list.append(i)

        for stock in long_list:
            data = self.getdatabyname(stock)
            order = self.order_target_size(data=data,target=10000)  
            self.order_list.append(order)

        for stock in sell_list:
            data = self.getdatabyname(stock)
            if self.getposition(data).size > 0:
                od = self.close(data=data)
                self.order_list.append(od)  # 记录卖出订单

    def back(self):
        return self.call
    
    # 交易记录日志（可省略，默认不输出结果）

    def log(self, txt, dt=None, doprint=False):
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()},{txt}')

    def notify_order(self, order):
        # 未被处理的订单
        if order.status in [order.Submitted, order.Accepted]:
            return
        # 已经处理的订单
        if order.status in [order.Completed, order.Canceled, order.Margin]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, ref:%.0f，Price: %.2f, Cost: %.2f, Comm %.2f, Size: %.2f, Stock: %s' %
                    (order.ref,  # 订单编号
                     order.executed.price,  # 成交价
                     order.executed.value,  # 成交额
                     order.executed.comm,  # 佣金
                     order.executed.size,  # 成交量
                     order.data._name))  # 股票名称
            else:  # Sell
                self.log('SELL EXECUTED, ref:%.0f, Price: %.2f, Cost: %.2f, Comm %.2f, Size: %.2f, Stock: %s' %
                         (order.ref,
                          order.executed.price,
                          order.executed.value,
                          order.executed.comm,
                          order.executed.size,
                          order.data._name))


# 初始资金 100,000,000
cerebro.broker.setcash(cash)
# 佣金，双边各 0.0003
cerebro.broker.setcommission(commission=0.0003)
# 滑点：双边各 0.0001
cerebro.broker.set_slippage_perc(perc=0.0001)

cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='pnl')  # 返回收益率时序数据
cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='_AnnualReturn')  # 年化收益率
cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='_SharpeRatio')  # 夏普比率
cerebro.addanalyzer(bt.analyzers.DrawDown, _name='_DrawDown')  # 回撤

# 将编写的策略添加给大脑，别忘了 ！
cerebro.addstrategy(TestStrategy, printlog=True)

# 启动回测
result = cerebro.run()
# 从返回的 result 中提取回测结果
strat = result[0]
# 返回日度收益率序列
daily_return = pd.Series(strat.analyzers.pnl.get_analysis())
# 打印评价指标
print("--------------- AnnualReturn -----------------")
print(strat.analyzers._AnnualReturn.get_analysis())
print("--------------- SharpeRatio -----------------")
print(strat.analyzers._SharpeRatio.get_analysis())
print("--------------- DrawDown -----------------")
print(strat.analyzers._DrawDown.get_analysis())

res = pd.DataFrame(strat.back(),columns=['datetime','value','base_value'])

trace1 = go.Scatter(
                    x = res.datetime,   # 定义坐标轴的映射关系，将world_rank这一列作为x轴
                    y = res.value,    # 同理，将citations这一列作为y轴
                    mode = "lines",      # 我们要绘制折线图，所以将mode设置为“lines”
                    name = "strategy",  # 将这条折线命名为citations
                    marker = dict(color = 'rgba(16, 112, 2, 0.8)'), 
                    # maker用来定义点的性质，如颜色、大小等
                    text= res.value)
                    # 将university_name一列设置为悬停文本（鼠标悬停在图片上方显示的内容）

# 设置第二条折线trace2
trace2 = go.Scatter(
                    x = res.datetime,
                    y = res.base_value,
                    mode = "lines+markers", #绘制的折线图由散点连接而成，即lines+markers
                    name = "base",
                    marker = dict(color = 'rgba(80, 26, 80, 0.8)'),
                    text= res.base_value)

data = [trace1, trace2]

# 添加图层layout
layout = dict(title = 'Yield curve',
              # 设置图像的标题
              xaxis= dict(title= 'date',ticklen= 5,zeroline= False)
              # 设置x轴名称，x轴刻度线的长度，不显示零线
             ) 

# 将data与layout组合为一个图像
fig = dict(data = data, layout = layout)
# 绘制图像
iplot(fig)
