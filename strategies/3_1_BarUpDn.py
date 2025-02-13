import yfinance as yf
import pandas as pd

def fetch_and_analyze_BarUpDn(stock_ticker, start_date, end_date):
    # 抓取股票數據
    data = yf.download(stock_ticker, start=start_date, end=end_date)

    if data.empty:
        print(f"No data found for {stock_ticker}.")
        return

    # 重置索引為單層索引
    data = data.reset_index()

    # 確保 'Close' 欄位存在並處理收盤價
    data['Prev_Close'] = data['Close'].shift(1)

    # 丟棄包含 NaN 的行
    data = data.dropna()

    # 強制將 'Close' 和 'Prev_Close' 設置為 Series 類型
    close = data['Close'].squeeze()
    prev_close = data['Prev_Close'].squeeze()

    # 定義漲跌信號
    signal = pd.Series(0, index=close.index)
    signal.loc[close > prev_close] = 1    # 上漲信號
    signal.loc[close < prev_close] = -1   # 下跌信號

    # 將信號寫回 DataFrame
    data['Signal'] = signal

    # 顯示結果
    print("\n--- BarUpDn Analysis ---")
    print(data[['Date', 'Close', 'Prev_Close', 'Signal']].to_string(index=False))

# 使用範例
if __name__ == "__main__":
    stock_ticker = "2330.TW"  # 指定股票代碼
    start_date = "2024-09-12"  # 開始日期
    end_date = "2024-09-30"    # 結束日期

    fetch_and_analyze_BarUpDn(stock_ticker, start_date, end_date)
