import yfinance as yf
import pandas as pd
import talib

def fetch_and_analyze_inside_bar(stock_ticker, start_date, end_date):
    # 抓取股票數據
    data = yf.download(stock_ticker, start=start_date, end=end_date)

    if data.empty:
        print(f"No data found for {stock_ticker}.")
        return

    # 重置索引並保留日期欄位
    data = data.reset_index()

    # 確保 High 和 Low 是 1D numpy 陣列
    high_prices = data['High'].values.flatten().astype(float)
    low_prices = data['Low'].values.flatten().astype(float)

    # 使用 TA-Lib 計算前一日的最高價與最低價
    prev_high = talib.SMA(high_prices, timeperiod=2)
    prev_low = talib.SMA(low_prices, timeperiod=2)

    # 轉換回 Pandas Series 並移動數據來獲取前一日數據
    data['Prev_High'] = pd.Series(prev_high, index=data.index).shift(1)
    data['Prev_Low'] = pd.Series(prev_low, index=data.index).shift(1)

    # 丟棄包含 NaN 的行
    data.dropna(inplace=True)

    # 確保所有數據為 1D Series，並轉換為 float
    data['High'] = pd.Series(data['High'].values.squeeze(), index=data.index)
    data['Prev_High'] = pd.Series(data['Prev_High'].values.squeeze(), index=data.index)
    data['Low'] = pd.Series(data['Low'].values.squeeze(), index=data.index)
    data['Prev_Low'] = pd.Series(data['Prev_Low'].values.squeeze(), index=data.index)

    # 確保數據索引對齊
    data['High'], data['Prev_High'] = data['High'].align(data['Prev_High'], axis=0, join='inner', copy=False)
    data['Low'], data['Prev_Low'] = data['Low'].align(data['Prev_Low'], axis=0, join='inner', copy=False)

    # 檢查數據形狀
    print(f"High shape: {data['High'].shape}, Prev_High shape: {data['Prev_High'].shape}")
    print(f"Low shape: {data['Low'].shape}, Prev_Low shape: {data['Prev_Low'].shape}")

    # 計算 Inside Bar 策略
    inside_bar_condition = (data['High'] <= data['Prev_High']) & (data['Low'] >= data['Prev_Low'])
    data['Signal'] = 0
    data.loc[inside_bar_condition, 'Signal'] = 1  # Inside Bar 符合條件

    # 顯示結果
    print("\n--- Inside Bar Analysis ---")
    print(data[['Date', 'High', 'Low', 'Prev_High', 'Prev_Low', 'Signal']].tail(10))

# 測試
stock_ticker = "2330.TW"  # 以台積電為例
start_date = "2024-09-12"
end_date = "2024-09-30"

fetch_and_analyze_inside_bar(stock_ticker, start_date, end_date)
