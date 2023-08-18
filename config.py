import os



# ALL_FEATURES = [
#     'open','high','low','close','volume','amount',
#     'macd','macds','macdh','kdjk','kdjd','kdjj',
#     'close_5_sma','close_10_sma','close_30_sma','close_60_sma','close_120_sma',
#     'cci','rsi_6','rsi_12','rsi_24'
# ]

# INDICATORS = [
#     'macd','macds','macdh','kdjk','kdjd','kdjj',
#     'close_5_sma','close_10_sma','close_30_sma','close_60_sma','close_120_sma',
#     'cci','rsi_6','rsi_12','rsi_24'
# ]

STOCK_LIST = lst = os.listdir('./data/inital_data')


INDICATORS = [
    'close_-1_d','change','log-ret',
    'close_5_sma','close_10_sma','close_20_sma','close_60_sma',
    'volume_5_sma','volume_10_sma','volume_20_sma','volume_30_sma','volume_60_sma','volume_120_sma','volume_240_sma'
]

ALL_FEATURES = ['open','high','low','close','volume','amount']+INDICATORS

