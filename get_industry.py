import json
import requests
from bs4 import BeautifulSoup
import time
from config import STOCK_LIST

t = open('./data/industry_data.json','w',encoding='utf8')

url = "https://xueqiu.com/hq"
headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; WOW64)"}


res = requests.get(url=url,headers=headers)
bs = BeautifulSoup(res.text,'html.parser')

# 保存所有行业类别
a = bs.find_all('a',attrs={'data-type':'undefined'})

# 访问主页，获取cookie
session = requests.Session()
session.get(url="https://xueqiu.com",headers=headers)

# 创建字典保存行业分类
industry_json = {}

# 遍历行业
for i in a:
    codes = []
    idx=str(i)[20:25]
    industry = i.text
    n=1
    while True:
        url_ = f'https://stock.xueqiu.com/v5/stock/screener/quote/list.json?page={n}&size=30&order=desc&order_by=percent&exchange=CN&market=CN&ind_code={idx}'
        
        # 带cookie的访问
        res_ = session.get(url=url_,headers=headers)
        js = res_.json()
        list_=js['data']['list']
        
        if list_:
            for x in list_:
                code=x['symbol']
                code = code[:2].lower()+'.'+code[2:]
                if code+'.csv' in STOCK_LIST:
                    codes.append(code)
            n+=1
        else:break

        time.sleep(2)
    if industry in industry_json:
        industry = industry+'_'
    if codes:
        industry_json[industry] = codes
    print(industry+' done')
print(industry_json)

# 保存为json
json.dump(industry_json,t,ensure_ascii=False)

        

