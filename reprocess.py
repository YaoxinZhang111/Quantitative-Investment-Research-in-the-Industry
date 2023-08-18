import pandas as pd
import os
import sys
sys.path.append('.')
import json
from stockstats import StockDataFrame as sdf
from config import ALL_FEATURES,INDICATORS,STOCK_LIST

# 读取行业分类及行业股票
file = open('./data/industry_data.json','r',encoding='utf8')
industrys = json.load(file)

def add_technical_indicator(data):
        # 增加技术指标
        temp_indictor = data
        indicator_data = sdf.retype(data)
        for i in INDICATORS:
            temp_indictor = indicator_data[i]
            indicator_data[i] = temp_indictor
        return indicator_data

def test_1(industry,data,code):
        # 清洗原始数据，并增加技术指标（预处理）
        print(f'dealing:{code}')
        write_path = './data/test_1/%s/%s.csv' % (industry ,code)
        df_data = data.copy()
        # 填充的方法补充零值
        df_data = df_data.fillna(method='pad')
        indicator_data = add_technical_indicator(df_data)
        try:
            indicator_data = indicator_data.drop(labels=['adjustflag','tradestatus','pettm','pbmrq','psttm','pcfncfttm','isst'], axis=1)
        except:pass
        indicator_data.to_csv(write_path)

for industry in industrys:
    industry_path = './data/test_1/%s' %industry
    if os.path.exists(industry_path):
        pass
    else:
        os.mkdir(industry_path)
    # 读取行业包含的股票列表
        code_list = industrys[industry]
    lasts_begin_data = '2009-01-01'
    for idx,code in enumerate(code_list):
        data_path = './data/inital_data/%s.csv' % code
        begin_time = pd.read_csv(data_path).iloc[0,0]
        # 移除2015-01-01之后才上市的股票
        if begin_time > '2015-01-01':
          code_list.pop(idx)  
        else:
            if begin_time > lasts_begin_data:
                lasts_begin_data = begin_time


    # 计算行业指数（均值法）
    sum_df = pd.DataFrame(columns=['date','open','high','low','close','volume','amount'])
    for idx,code in enumerate(code_list):
        data_path = './data/inital_data/%s.csv' % code
        open_df = pd.read_csv(data_path)
        open_df = open_df[open_df.date > lasts_begin_data]
        sum_df['date'] = open_df['date'].copy()
        sum_df.fillna(0,inplace=True)
        sum_ = lambda cloum:sum_df[cloum]+open_df[cloum]
        sum_df.open = sum_('open')
        sum_df.high = sum_('high')
        sum_df.low = sum_('low')
        sum_df.close = sum_('close')
        sum_df.volume = sum_('volume')
        sum_df.amount = sum_('amount')
        
        # 单只股票添加技术指标，并保存到所属行业
        test_1(industry,open_df,code)
        
    # 均值
    sum_df.iloc[:,1:]=sum_df.iloc[:,1:]/len(code_list)
    # 行业指数增加技术指标
    test_1(industry,sum_df,industry+'ex')
    