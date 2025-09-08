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
STOCK_LIST = [
    '2330', '2344', '1301', '2412', '3008', '2881', '2303', '2317', '2454', '2882',
    '2308', '2301', '2603', '2311', '2891', '2885', '3481', '4938', '2002', '2880',
    '1216', '2610', '1326', '1101', '3005', '2357', '1303', '2884', '2313', '2382',
    '2383', '2356', '5871', '2883', '1402', '1325', '2886', '2417', '2207', '2353',
    '2409', '2337', '2354', '2408', '1324', '3034', '3037', '1305', '2371', '2325'
]

def get_random_stock():
    """隨機選擇一支股票"""
    return random.choice(STOCK_LIST)

def fetch_stock_data(stock_code):
    """使用 yfinance 獲取股票數據並存成 CSV"""
    csv_path = os.path.join(DATA_DIR, f"{stock_code}.csv")
    if os.path.exists(csv_path):
        print(f"{stock_code} 的資料已存在，不再重新下載。")
        return True

    stock_code_yf = stock_code + ".TW"
    stock = yf.Ticker(stock_code_yf)
    
    try:
        df = stock.history(period="2y")
    except yf.exceptions.YFRateLimitError as e:
        print(f"[RateLimitError] 嘗試太頻繁，請稍後再試：{e}")
        return False
    except Exception as e:
        print(f"[錯誤] 無法獲取 {stock_code} 的數據: {e}")
        return False

    if df.empty:
        print(f"無法獲取 {stock_code} 的數據")
        return False

    df.reset_index(inplace=True)
    df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]

    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

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
