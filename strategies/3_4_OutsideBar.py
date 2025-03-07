import yfinance as yf
import pandas as pd

def fetch_and_analyze_OutsideBar(stock_ticker, start_date, end_date):
    try:
        data = yf.download(stock_ticker, start=start_date, end=end_date, interval="1d", progress=False, auto_adjust=False)
    except Exception as e:
        print(f"Error downloading data: {e}")
        return

    if data.empty:
        print(f"No data found for {stock_ticker}.")
        return

    # 重置索引並檢查欄位名稱
    data = data.reset_index()
    
    # 確保數據包含必要欄位
    required_cols = ["Date", "High", "Low"]
    for col in required_cols:
        if col not in data.columns:
            print(f"❌ 缺少必要欄位 {col}，數據結構可能異常")
            print("數據欄位：", data.columns)
            return

    # 設置前一天的高低價
    data['Prev_High'] = data['High'].shift(1)
    data['Prev_Low'] = data['Low'].shift(1)

    # **對齊 DataFrame 以防止錯誤**
    data, shifted = data.align(data.shift(1), axis=0, copy=False)

    # 計算 Outside Bar 訊號
    outside_bar_signal = (data['High'] > shifted['High']) & (data['Low'] < shifted['Low'])
    data['Signal'] = outside_bar_signal.astype(int)

    # 移除 NaN 值
    data = data.dropna()

    # 顯示結果
    print("\n--- Outside Bar Analysis ---")
    print(data[['Date', 'High', 'Low', 'Prev_High', 'Prev_Low', 'Signal']].to_string(index=False))

if __name__ == "__main__":
    stock_ticker = "2330.TW"
    start_date = "2024-09-12"
    end_date = "2024-09-30"
    fetch_and_analyze_OutsideBar(stock_ticker, start_date, end_date)
