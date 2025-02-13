import yfinance as yf
import pandas as pd

def fetch_and_analyze_consecutive(stock_ticker, start_date, end_date, consecutive_days=3):
    # 抓取股票數據
    data = yf.download(stock_ticker, start=start_date, end=end_date)

    if data.empty:
        print(f"No data found for {stock_ticker}.")
        return

    # 重置索引為單層索引，避免 MultiIndex 問題
    data = data.reset_index()

    # 計算每日漲跌變化
    data['Price_Change'] = data['Close'].diff()

    # 判斷漲跌，漲+1，跌-1
    data['Trend'] = data['Price_Change'].apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))

    # 計算連續天數
    data['Consecutive_Up'] = (data['Trend'] == 1).astype(int).groupby(data['Trend'].ne(1).cumsum()).cumsum()
    data['Consecutive_Down'] = (data['Trend'] == -1).astype(int).groupby(data['Trend'].ne(-1).cumsum()).cumsum()

    # 產生信號
    data['Signal'] = 0
    data.loc[data['Consecutive_Up'] >= consecutive_days, 'Signal'] = 1  # 上漲信號
    data.loc[data['Consecutive_Down'] >= consecutive_days, 'Signal'] = -1  # 下跌信號

    # 顯示結果
    print("\n--- Consecutive Up/Down Strategy Analysis ---")
    print(data[['Date', 'Close', 'Consecutive_Up', 'Consecutive_Down', 'Signal']].to_string(index=False))

# 使用範例
if __name__ == "__main__":
    stock_ticker = "2330.TW"  # 指定股票代碼
    start_date = "2024-09-12"  # 開始日期
    end_date = "2024-09-30"    # 結束日期

    fetch_and_analyze_consecutive(stock_ticker, start_date, end_date)
