import yfinance as yf
import numpy as np
import pandas as pd
import talib  

def fetch_and_analyze_keltner_channel(stock_ticker, start_date, end_date, initial_capital=100000, ema_period=20, atr_multiplier=1, volume_period=20):
    
    # 抓取股票數據
    data = yf.download(stock_ticker, start=start_date, end=end_date)
    

    # 檢查並轉換 'Close', 'High', 'Low' 欄位為數值型
    required_columns = ['Close', 'High', 'Low']
    for col in required_columns:
        if col not in data.columns:
            print(f"數據中缺少 '{col}' 列，無法計算 Keltner Channel！")
            return

    

    if data[required_columns].isna().any().any():  # 檢查是否有缺失值
        print("數據中包含缺失值，將自動刪除 NaN 行。")
        # 檢查並刪除 NaN 行
        data = data.dropna(subset=required_columns)

    if data.empty:
        print(f"找不到股票代碼 {stock_ticker} 的數據，請確認代碼或日期是否正確。")
        return

    # 使用 talib 計算 EMA 和 ATR
    close_prices = data['Close'].values.flatten()
    high_prices = data['High'].values.flatten()
    low_prices = data['Low'].values.flatten()
    

    data['EMA'] = talib.EMA(close_prices, timeperiod=ema_period)
    data['ATR'] = talib.ATR(high_prices, low_prices, close_prices, timeperiod=ema_period)
    

    # 計算 Keltner Channel 上軌和下軌
    data['Upper Band'] = data['EMA'] + atr_multiplier * data['ATR']
    data['Lower Band'] = data['EMA'] - atr_multiplier * data['ATR']
    

    # 確保 'Volume' 列存在並處理
    if 'Volume' not in data.columns:
        print(f"警告：資料中未找到 'Volume' 列。請檢查下載的數據是否正確。")
        return

    volume = data['Volume']
    
    # 計算過去 volume_period 天的平均成交量
    data['Avg Volume'] = volume.rolling(window=volume_period).mean()

    # 填充 NaN 值（或選擇刪除）
    data['Lower Band'] = data['Lower Band'].fillna(0)  # 填充為 0
    data['Avg Volume'] = data['Avg Volume'].fillna(0)  # 填充為 0

    
    # 展平索引
    data = data.reset_index()
    

    # 將所有數據轉為純 Series
    aligned_close = data['Close']['2330.TW']
    aligned_lower_band = data['Lower Band'].copy()
    aligned_upper_band = data['Upper Band'].copy()
    aligned_volume = data['Volume']['2330.TW']
    aligned_avg_volume = data['Avg Volume'].copy()
    
    
    # 使用 align 方法對齊索引
    aligned_close, aligned_lower_band = aligned_close.align(aligned_lower_band, axis=0)
    aligned_volume, aligned_avg_volume = aligned_volume.align(aligned_avg_volume, axis=0)
    aligned_upper_band = aligned_upper_band.reindex(aligned_close.index)

   
    # 使用比較操作判斷信號
    buy_condition = (aligned_close < aligned_lower_band) & (aligned_volume > aligned_avg_volume)
    sell_condition = (aligned_close > aligned_upper_band) & (aligned_volume > aligned_avg_volume)
    
    # 初始化信號列
    data['Signal'] = 0

    # 將條件結果應用到原始數據
    data.loc[buy_condition, 'Signal'] = 1  # 買入信號
    data.loc[sell_condition, 'Signal'] = -1  # 賣出信號

    # 計算交易績效
    data['Daily Returns'] = data['Close'].pct_change()
    data['Strategy Returns'] = data['Signal'].shift(1) * data['Daily Returns']
    data['Equity Curve'] = (1 + data['Strategy Returns']).cumprod() * initial_capital
    
    # 計算績效指標
    net_profit = data['Equity Curve'].iloc[-1] - initial_capital  # 總淨利
    max_equity_drawdown = (data['Equity Curve'].cummax() - data['Equity Curve']).max()  # 最大回撤
    total_trades = (data['Signal'] != 0).sum()  # 總交易次數
    profitable_trades = (data['Strategy Returns'] > 0).sum()  # 盈利交易數
    percent_profitable = (profitable_trades / total_trades) * 100 if total_trades > 0 else 0  # 勝率
    profit_factor = data.loc[data['Strategy Returns'] > 0, 'Strategy Returns'].sum() / abs(data.loc[data['Strategy Returns'] < 0, 'Strategy Returns'].sum()) if abs(data.loc[data['Strategy Returns'] < 0, 'Strategy Returns'].sum()) > 0 else float('inf')
    

    # 顯示結果
    print("\n--- Keltner Channel Strategy with Dynamic Volume Threshold ---")
    print(data[['Date','Close', 'EMA', 'Upper Band', 'Lower Band', 'Volume', 'Avg Volume', 'Signal']].tail(20))  
    print("\n--- Performance Metrics ---")
    print(f"Net Profit: {net_profit:.2f}")
    print(f"Max Equity Drawdown: {max_equity_drawdown:.2f}")
    print(f"Total Trades: {total_trades}")
    print(f"Percent Profitable: {percent_profitable:.2f}%")
    print(f"Profit Factor: {profit_factor:.2f}")
    
# 使用範例
if __name__ == "__main__":
    stock_ticker = "2330.TW"  # 指定股票代碼
    start_date = "2024-01-01"  # 開始日期
    end_date = "2024-12-30"    # 結束日期
    fetch_and_analyze_keltner_channel(stock_ticker, start_date, end_date)
