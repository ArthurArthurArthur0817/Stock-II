import yfinance as yf
import numpy as np
import pandas as pd
import talib

def run(stock_symbol, initial_capital, window=5, num_std_dev=1, period=5):
     # 抓取股票數據
    data = yf.download(stock_symbol, period="3mo")
    
    # 檢查並轉換 'Close' 欄位為數值型
    close_column = ('Close', stock_symbol)
    if close_column not in data.columns:
        print(f"數據中缺少 'Close' 列，無法計算移動平均！")
        return

    

    if data[close_column].isna().any():  # 使用 .any() 來檢查是否有缺失值
        print("數據中包含缺失值，將自動刪除 NaN 行。")
        # 檢查並刪除 NaN 行
        data = data.dropna(subset=[close_column])

    if data.empty:
        print(f"找不到股票代碼 {stock_symbol} 的數據，請確認代碼或日期是否正確。")
        return


     # 使用 talib 計算布林帶
    close_prices = data[close_column]
    upper_band, middle_band, lower_band = talib.BBANDS(close_prices, timeperiod=window, nbdevup=num_std_dev, nbdevdn=num_std_dev, matype=0)

    # 將布林帶數據加入到 DataFrame 中
    data[('Moving Average', stock_symbol)] = middle_band
    data[('Upper Band', stock_symbol)] = upper_band
    data[('Lower Band', stock_symbol)] = lower_band

    # 確保 'Volume' 列存在並處理
    volume_column = ('Volume', stock_symbol)
    if volume_column not in data.columns:
        print(f"警告：資料中未找到 'Volume' 列。請檢查下載的數據是否正確。")
        return

    volume = data[volume_column]
    
    # 計算過去 period 天的平均成交量
    data[('Avg Volume', stock_symbol)] = volume.rolling(window=period).mean()

    # 設定買賣信號，考慮成交量
    data['Signal'] = 0  # 預設無信號

    # 使用 MultiIndex 正確處理比較操作
    data.loc[(data[close_column] < data[('Lower Band', stock_symbol)]) & 
             (data[volume_column] > data[('Avg Volume', stock_symbol)]), 'Signal'] = 1  # 買入信號

    data.loc[(data[close_column] > data[('Upper Band', stock_symbol)]) & 
             (data[volume_column] > data[('Avg Volume', stock_symbol)]), 'Signal'] = -1  # 賣出信號


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
    
    # 將績效指標整理成字典
    result = {
        'latest_Close': round(data['Close'].iloc[-1].iloc[0], 2),
        'latest_Volume': round(data['Volume'].iloc[-1].iloc[0], 2),
        'latest_MA': round(data['Moving Average'].iloc[-1].iloc[0], 2),
        'latest_Upper_Band': round(data['Upper Band'].iloc[-1].iloc[0], 2),
        'latest_Lower_Band': round(data['Lower Band'].iloc[-1].iloc[0], 2),
        "Net Profit": f"{net_profit:.2f}",
        "Max Equity Drawdown": f"{max_equity_drawdown:.2f}",
        "Total Trades": total_trades,
        "Percent Profitable": f"{percent_profitable:.2f}%",
        "Profit Factor": f"{profit_factor:.2f}"
    }

    # 儲存結果到 TXT
    save_analysis_to_txt(result, data, stock_symbol)

    return result

def save_analysis_to_txt(result, data, stock_symbol):
    filename = "analysis_results.txt"

    with open(filename, "w", encoding="utf-8") as f:
        # 寫入 Bollinger Bands Analysis
        f.write("--- Bollinger Bands Analysis ---\n")
        f.write("Price        Close    MA    Upper Band    Lower Band    Signal\n")
        f.write("Ticker                           \n")
        f.write("Date                                \n")
        

        # 根據 stock_symbol 建立正確的列名
        close_col = ('Close', stock_symbol)
        ma_col = ('Moving Average', stock_symbol)
        upper_band_col = ('Upper Band', stock_symbol)
        lower_band_col = ('Lower Band', stock_symbol)
        
        # 確保需要的列存在
        if all(col in data.columns for col in [close_col, ma_col, upper_band_col, lower_band_col]):
            # 保存最後 10 行數據
            for index, row in data.tail(10).iterrows():
                f.write(f"{index.date()}  {row[close_col]:.2f}  {row[ma_col]:.2f}  {row[upper_band_col]:.2f}  {row[lower_band_col]:.2f}  {int(row['Signal'])}\n")
       
        else:
            f.write("布林通道數據缺失。\n\n")

        # 寫入 Performance Summary
        f.write("--- Performance Summary ---\n")
        for key, value in result.items():
            f.write(f"{key}: {value}\n")
   
    print(f"結果已寫入 {filename}")