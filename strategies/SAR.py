import yfinance as yf
import pandas as pd
import talib

# 設定顯示所有行
pd.set_option('display.max_rows', None)

# 定義抓取並分析 SAR 的函數
def fetch_and_analyze_sar(ticker, start_date, end_date, interval='1d'):

    # 從 Yahoo Finance 抓取資料
    data = yf.download(ticker, start=start_date, end=end_date, interval=interval)

    # 檢查資料是否抓取成功，並顯示原始資料
    if data.empty:
        print(f"No data found for {ticker} between {start_date} and {end_date}.")
        return

    # 如果資料是 MultiIndex，將其展平為單一層級
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [' '.join(col).strip() for col in data.columns.values]

    # 確保 'High' 和 'Low' 欄位存在並使用正確的欄位名稱
    high_column = f"High {ticker}"
    low_column = f"Low {ticker}"

    # 轉換為 numpy 陣列並確保一維
    high_prices = data[high_column].values.flatten()
    low_prices = data[low_column].values.flatten()

    # 計算 Parabolic SAR
    data['SAR'] = talib.SAR(high_prices, low_prices, acceleration=0.02, maximum=0.2)

    # 如果 'SAR' 欄位有 NaN 值，將其填充為 0 或其他合適的數值
    data['SAR'].fillna(0, inplace=True)

    # 確保 SAR 和 Close 欄位都存在，並移除包含 NaN 的行
    close_column = f"Close {ticker}"
    if close_column in data.columns:
        data.dropna(subset=[close_column], inplace=True)
    else:
        print(f"No '{close_column}' column found!")

    # 檢查 SAR 交叉（例如，當 SAR > Close 時產生賣出信號）
    data['Signal'] = 0  # 預設信號為 0
    data.loc[data['SAR'] > data[close_column], 'Signal'] = -1  # SAR 大於收盤價時，為賣出信號
    data.loc[data['SAR'] <= data[close_column], 'Signal'] = 1  # SAR 小於等於收盤價時，為買入信號

    # 找出 SAR 的交叉點
    data['Crossover'] = data['Signal'].diff()

    # 顯示交叉信號
    print("\n--- SAR Crossover Signals ---")
    print(data[[close_column, 'SAR', 'Signal', 'Crossover']])

    return data

# 你的股票資料設定
stock_ticker = '2330.TW'  # 設定股票代碼
start_date = '2024-12-30'  # 設定開始日期
end_date = '2025-01-19'    # 設定結束日期

# 呼叫函數來抓取並分析 SAR 交叉
result = fetch_and_analyze_sar(stock_ticker, start_date, end_date)
