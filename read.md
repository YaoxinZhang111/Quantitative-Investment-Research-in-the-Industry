+ 1 运行 [get_stock_data.py](./get_stock_data.py)用来从baostock下载数据,下载后的数据保存至 './data/initial_data'

+ 2 运行[get_industry.py](./get_industry.py),从雪球爬取行业分类，爬取后的json文件保存在'./data'

+ 3 运行[reprocess.py](./reprocess.py),对原始数据进行预处理，处理后数据储存在'./data/test_1'

+ 4 运行[main.py](./main.py),进行回测。回测内调用函数

```py
def backtrader(cut_loss,target_profit,save=False):
    pass
```
> cut_loss:止损点（注意添加负号）
>> target_profit:止盈点
>>> save：布尔值，默认False，若True则在'./log'中储存回测结果

+ 说明： [config.py](./config.py) 文件配置获取股票列表以及配置预处理时需要的的指标，详细可使用指标查询[stockstats](https://pypi.org/project/stockstats/0.3.1/)

+ log说明： profit为盈利的操作，deficit为亏损的操作，unseated为回测结束仍为平仓