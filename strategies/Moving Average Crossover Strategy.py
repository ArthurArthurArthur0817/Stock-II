import yfinance as yf
import pandas as pd
import talib

# 設定顯示所有行
pd.set_option('display.max_rows', None)

# 定義抓取並分析移動平均線交叉的函數
def fetch_and_analyze_ma_crossover(ticker, start_date, end_date, interval='1d'):
    print(f"Fetching data for {ticker} from {start_date} to {end_date} with interval {interval}...")

    # 從 Yahoo Finance 抓取資料
    data = yf.download(ticker, start=start_date, end=end_date, interval=interval)

    # 檢查資料是否抓取成功，並顯示原始資料
    if data.empty:
        print(f"No data found for {ticker} between {start_date} and {end_date}.")
        return

    # 計算短期與長期移動平均
    short_ma_period = 5  # 短期移動平均的期間
    long_ma_period = 20  # 長期移動平均的期間
    
    # 轉換為 numpy 陣列並確保一維
    close_prices = data['Close'].values.flatten()  # 確保是一維陣列

    # 計算簡單移動平均（SMA）
    data['Short_MA'] = talib.SMA(close_prices, timeperiod=short_ma_period)
    data['Long_MA'] = talib.SMA(close_prices, timeperiod=long_ma_period)

    # 檢查移動平均的下交叉點
    data['Signal'] = 0  # 預設信號為 0
    data.loc[data['Short_MA'] > data['Long_MA'], 'Signal'] = 1  # 短期MA大於長期MA時，設為 1
    data.loc[data['Short_MA'] <= data['Long_MA'], 'Signal'] = -1  # 短期MA小於等於長期MA時，設為 -1

    # 找出交叉點（訊號變化）
    data['Crossover'] = data['Signal'].diff()

    # 顯示交叉信號
    print("\n--- Crossover Signals ---")
    print(data[['Close', 'Short_MA', 'Long_MA', 'Signal', 'Crossover']])

    return data

# 你的股票資料設定
stock_ticker = '2330.TW'  # 設定股票代碼
start_date = '2024-10-30'  # 設定開始日期
end_date = '2025-01-19'    # 設定結束日期

# 呼叫函數來抓取並分析移動平均交叉
result = fetch_and_analyze_ma_crossover(stock_ticker, start_date, end_date)