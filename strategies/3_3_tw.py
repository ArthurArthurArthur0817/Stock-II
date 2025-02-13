import yfinance as yf
import pandas as pd

def fetch_and_analyze_inside_bar(stock_ticker, start_date, end_date):
    # 抓取台股數據，關閉自動調整來獲取未調整數據
    data = yf.download(stock_ticker, start=start_date, end=end_date, group_by='ticker', interval="1d", auto_adjust=False)

    if data.empty:
        print(f"No data found for {stock_ticker}.")
        return

    # 列印下載的欄位名稱
    print("Downloaded columns:", data.columns)

    # 轉換 MultiIndex 欄位名稱為單層索引，保留原始格式
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = ['_'.join([str(i) for i in col]).strip().lower() for col in data.columns.values]

    print("Processed columns:", data.columns)

    # 列印原始數據以比對
    print("\n--- Raw Data Preview ---")
    print(data.head())

    # 修正股票代號格式（保持 .tw 不變）
    ticker_suffix = stock_ticker.lower()

    # 修改欄位名稱檢查，對應到轉換後的格式
    required_columns = [f'{ticker_suffix}_high', f'{ticker_suffix}_low', f'{ticker_suffix}_close']
    missing_columns = [col for col in required_columns if col not in data.columns]
    if missing_columns:
        raise KeyError(f"Missing required columns: {missing_columns}")

    # 計算 Inside Bar (前一天的最高/最低價)
    data['prev_high'] = data[f'{ticker_suffix}_high'].shift(1)
    data['prev_low'] = data[f'{ticker_suffix}_low'].shift(1)

    # 刪除 NaN 值（先確保欄位存在）
    data.dropna(subset=['prev_high', 'prev_low', f'{ticker_suffix}_high', f'{ticker_suffix}_low'], inplace=True)

    # Inside Bar 判斷邏輯（是否形成 inside bar）
    data['inside_bar'] = (data[f'{ticker_suffix}_high'] <= data['prev_high']) & (data[f'{ticker_suffix}_low'] >= data['prev_low'])

    # 初始化信號為 0
    data['signal'] = 0

    # 設定買賣信號
    data.loc[data['inside_bar'] & (data[f'{ticker_suffix}_close'] > data['prev_high']), 'signal'] = 1  # 向上突破買入
    data.loc[data['inside_bar'] & (data[f'{ticker_suffix}_close'] < data['prev_low']), 'signal'] = -1  # 向下突破賣出


    # 顯示結果
    print("\n--- Inside Bar Analysis ---")
    print(data[[f'{ticker_suffix}_close', f'{ticker_suffix}_high', f'{ticker_suffix}_low', 'prev_high', 'prev_low', 'inside_bar', 'signal']].tail(10))

if __name__ == "__main__":
    stock_ticker = "2330.TW"  # 台積電台股代號
    start_date = "2024-09-01"  # 開始日期
    end_date = "2024-09-30"    # 結束日期

    fetch_and_analyze_inside_bar(stock_ticker, start_date, end_date)
