import pandas as pd
import datetime
import json
import time
import os
from pandas.tseries.offsets import DateOffset
file = open('./data/industry_data.json','rb')
industrys = json.load(file)



def backtrade(cut_loss,target_profit,save=False):
    # 回测主程序，参数为：止损点，止盈点，是否保存回测日志
    
    # 日志文件列表
    profit_list =[]
    deficit_list =[]
    unsettled_list =[]

    for industry in industrys:
        print(f'dealing:{industry}')
        # 读取行业股票列表
        stocks = os.listdir(f'./data/test_1/{industry}')
        stocks.remove(f'{industry}ex.csv')
        # 读取行业指数
        industry_file_path = './data/test_1/%s/%sex.csv' % (industry ,industry)
        df = pd.read_csv(industry_file_path)
        df.dropna(inplace=True)
        df=df.drop(index=df[(df['date']=='0')].index.tolist())
        
        df['date'] = pd.to_datetime(df['date'],format='%Y-%m-%d')
        
        # 判断是否符合要求
        sift_df=df[(df['volume_20_sma']>df['volume_120_sma']) & (df['volume_20_sma']>df['volume_240_sma']) & (df['volume_30_sma']>df['volume_120_sma']) & (df['volume_30_sma']>df['volume_240_sma']) & (df['volume_60_sma']>df['volume_120_sma']) & (df['volume_60_sma']>df['volume_240_sma'])]
        sift_df.reset_index(inplace=True)

        # 将符合条件的日期加入到购买日期
        buy_date = []
        for i in range(len(sift_df)):
            now_date = sift_df.loc[i,'date']
            if i>0:
                last_date = sift_df.loc[i-1,'date']
                if (now_date - last_date).days > 8:
                    buy_date.append(now_date)
            else:
                buy_date.append(now_date)
                
        # 遍历行业内每一只股票
        for stock in stocks:
            
            stock_path = './data/test_1/%s/%s' % (industry ,stock)
        
            df_ = pd.read_csv(stock_path,parse_dates=['date'])
                    
            # 遍历每一个购买日期
            for date_ in buy_date:
                buy_df = df_[(df_.date>=date_) & (df_.date < date_+DateOffset(days=30))]
                buy_df.reset_index(inplace=True)
                for i in range(30):
                    try:
                        back_day=buy_df.iloc[i,:]
                    except:
                        idx=False
                        break
                    if (back_day['volume']>back_day['volume_5_sma']) & (back_day['volume']>back_day['volume_10_sma']):
                        idx=i
                        break
                    if i==29:
                        idx=False
                if idx:
                    buy_df=buy_df.iloc[idx:,:]
                else:break
                
                buy_df.reset_index(inplace=True)
                
                buy_price = buy_df.loc[0,'close']
                date_ = buy_df.loc[0,'date']

                for i in range(len(buy_df)):
                    today_price = buy_df.loc[i,'close']
                    day = buy_df.loc[i,'date']
                    
                    pct = (today_price/buy_price - 1 )
                    
                    if pct < cut_loss:
                        deficit_list.append([industry,stock,str(date_)[:10],str(day)[0:10],float(buy_price),float(today_price),float(pct)])
                        break
                    elif pct > target_profit:
                        profit_list.append([industry,stock,str(date_)[:10],str(day)[0:10],float(buy_price),float(today_price),float(pct)])
                        break
                    elif day > date_+DateOffset(days=7):
                        deficit_list.append([industry,stock,str(date_)[:10],str(day)[0:10],float(buy_price),float(today_price),float(pct)])
                        break
                    else:pass
                    
                    if i+1 == len(buy_df):
                        unsettled_list.append([industry,stock,str(date_)[:10],str(day)[0:10],float(buy_price),float(today_price),float(pct)])
                    else:pass
            
    win_rate = len(profit_list)/(len(profit_list)+len(deficit_list))
    ave_interest_rate = (len(profit_list)*target_profit + len(deficit_list)*cut_loss)/(len(profit_list)+len(deficit_list))
    turn_over = len(profit_list)+len(deficit_list)+len(unsettled_list)
    
    if save:
        pro_df = pd.DataFrame(profit_list,columns=['industry','code','buy_date','sell_date','buy_price','sell_price','pct_reward'])
        
        loss_df = pd.DataFrame(deficit_list,columns=['industry','code','buy_date','sell_date','buy_price','sell_price','pct_reward'])
        unsetted_df = pd.DataFrame(unsettled_list,columns=['industry','code','buy_date','sell_date','buy_price','sell_price','pct_reward'])

        pro_df.to_csv('./log/profit.csv',index=False)
        loss_df.to_csv('./log/deficit.csv',index=False)
        unsetted_df.to_csv('./log/unsetted.csv',index=False)

    return cut_loss,target_profit,win_rate,ave_interest_rate,turn_over


if __name__ == '__main__':
    # ending_list = []
    # for cut_loss in range(0,-20,-1):
    #     for target in range(10,100,5):
    #         ending=backtrade(cut_loss=cut_loss/100,target_profit=target/100,save=False)
    #         ending_list.append(list(ending))

    # ending_df = pd.DataFrame(ending_list,columns=['cut_loss','target_profit','win_rate','ave_interest_rate','turn_over'])
    # ending_df.to_csv('./log/backtrade.csv',index=False)

    backtrade(-10,0.08,True)