import os
import pandas as pd
import yfinance as yf
import mplfinance as mpf
import random
import matplotlib
from flask import Flask, render_template, session, jsonify

matplotlib.use('Agg')  # 避免 Tkinter 問題

app = Flask(__name__)
app.secret_key = 'your_secret_key'

DATA_DIR = './data'
STOCK_LIST = ['2330', '2344','0050','1301']

def get_random_stock():
    """隨機選擇一支股票"""
    return random.choice(STOCK_LIST)

def fetch_stock_data(stock_code):
    """使用 yfinance 獲取股票數據並存成 CSV"""
    stock_code_yf = stock_code + ".TW"  # 台股代碼需要加 .TW
    stock = yf.Ticker(stock_code_yf)
    df = stock.history(period="2y")  # 取最近 3 年數據

    if df.empty:
        print(f"無法獲取 {stock_code} 的數據")
        return False
    
    df.reset_index(inplace=True)
    df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
    
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    csv_path = os.path.join(DATA_DIR, f"{stock_code}.csv")
    df.to_csv(csv_path, index=False)
    print(f"已儲存 {stock_code} 股票數據至 {csv_path}")
    return True

def plot_stock_data(stock_code, start_index):
    """繪製股票走勢圖"""
    csv_path = os.path.join(DATA_DIR, f'{stock_code}.csv')
    if not os.path.exists(csv_path):
        return None  # 檔案不存在

    df = pd.read_csv(csv_path, parse_dates=['Date'], index_col='Date')
    
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
