import os
import pandas as pd
import mplfinance as mpf
import twstock
import random
import matplotlib
matplotlib.use('Agg')  # 這行很重要，避免 Tkinter 問題

DATA_DIR = './data'
STOCK_LIST = ['0050','2330']

def get_random_stock():
    """隨機選擇一支股票"""
    return random.choice(STOCK_LIST)

def plot_stock_data(stock_code, start_index):
    """繪製股票走勢圖"""
    csv_path = os.path.join(DATA_DIR, f'{stock_code}.csv')
    if not os.path.exists(csv_path):
        return None  # 檔案不存在

    df = pd.read_csv(csv_path, parse_dates=['Date'], index_col='Date')
    df.rename(columns={'Turnover': 'Volume'}, inplace=True)

    end_index = start_index + 10
    df_subset = df.iloc[start_index:end_index]

    if df_subset.empty:
        return None

    mc = mpf.make_marketcolors(up='r', down='g', inherit=True)
    s = mpf.make_mpf_style(base_mpf_style='yahoo', marketcolors=mc)

    kwargs = dict(type='candle', mav=(5, 20, 60), volume=True, figratio=(10, 8), figscale=0.75, style=s)
    
    static_path = os.path.join("static", f"{stock_code}_chart.png")  
    mpf.plot(df_subset, **kwargs, savefig=static_path)

    return static_path


def fetch_stock_data(stock_code):
    """爬取股票數據並存成 CSV"""
    stock = twstock.Stock(stock_code)
    target_price = stock.fetch_from(2020, 1)  # 取2020年1月到現在的交易資料
    print(f"股票 {stock_code} 獲取資料筆數: {len(target_price)}")  # 新增這行

    if not target_price:  # 如果沒有數據，回傳錯誤
        print(f"無法獲取 {stock_code} 的數據")
        return

    columns = ['Date', 'Capacity', 'Turnover', 'Open', 'High', 'Low', 'Close', 'Change', 'Transaction']
    df = pd.DataFrame(target_price, columns=columns)

    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    csv_path = os.path.join(DATA_DIR, f'{stock_code}.csv')
    df.to_csv(csv_path, index=False)