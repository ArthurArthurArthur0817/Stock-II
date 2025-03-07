import yfinance as yf
import talib
import pandas as pd
import numpy as np

def run(stock_symbol, initial_capital, period=5):
    # 抓取最近 3 個月的股票資料
    data = yf.download(stock_symbol, period="3mo")
    
    if data.empty:
        print(f"No data found for {stock_symbol}.")
        return

    # 展開 MultiIndex，只選取 Price 層級的列名
    data.columns = data.columns.get_level_values(0)

    # 確保需要的列名存在
    required_columns = ['High', 'Low', 'Close']
    if not all(col in data.columns for col in required_columns):
        print(f"Missing required columns: {', '.join(col for col in required_columns if col not in data.columns)}")
        return

     
   
    # 檢查 NaN 值，並丟棄包含 NaN 的行
    data = data.dropna(subset=['High', 'Low'])

    # 確保 'High' 和 'Low' 是 pandas.Series 並轉為 numpy.ndarray
    high_prices = data['High'].values  # 轉為 numpy.ndarray
    low_prices = data['Low'].values   # 轉為 numpy.ndarray

    # 確保 high_prices 和 low_prices 是一維陣列
    high_prices = np.asarray(data['High']).flatten()  # 強制轉為一維
    low_prices = np.asarray(data['Low']).flatten()    # 強制轉為一維

    data['High_Channel'] = talib.MAX(high_prices, timeperiod=period)
    data['Low_Channel'] = talib.MIN(low_prices, timeperiod=period)

   


    # 確保通道數據已完整 (過濾掉含有 NaN 的行)
    data.dropna(subset=['High_Channel', 'Low_Channel'], inplace=True)

    # 定義信號
    data['Signal'] = 0
    data.loc[data['Close'] > data['High_Channel'].shift(1), 'Signal'] = 1  # 買入信號
    data.loc[data['Close'] < data['Low_Channel'].shift(1), 'Signal'] = -1  # 賣出信號

    # 計算持倉：連續持倉的狀態
    data['Position'] = data['Signal'].replace(0, np.nan).ffill()

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
    

    # 結果輸出
    result = {
        'latest_Close': round(data['Close'].iloc[-1], 2),
        'latest_High_Channel': round(data['High_Channel'].iloc[-1], 2),
        'latest_Low_Channel': round(data['Low_Channel'].iloc[-1], 2),
        'net_profit': round(net_profit, 2),
        'max_drawdown': round(max_equity_drawdown, 2),
        'total_trades': total_trades,
        'percent_profitable': round(percent_profitable, 2),
        'profit_factor': round(profit_factor, 2),
        
    }

    # 保存結果到檔案
    save_analysis_to_txt(result, data, stock_symbol)

    return result


def save_analysis_to_txt(result, data, stock_symbol):
    filename = "analysis_results.txt"

    with open(filename, "w", encoding="utf-8") as f:
        # 寫入通道分析資料
        f.write("--- Channel Breakout Analysis ---\n")
        f.write("Price       Close      HighChannel    LowChannel   Signal\n")
        f.write("Ticker                           \n")
        f.write("Date                                \n")
        
        # 保存最後 10 行資料
        for index, row in data.tail(10).iterrows():
            f.write(f"{index.date()}  {row['Close']:.2f}  {row['High_Channel']:.2f}  {row['Low_Channel']:.2f}  {int(row['Signal'])}\n")

        # 寫入績效總結
        f.write("\n--- Performance Summary ---\n")
        for key, value in result.items():
            f.write(f"{key}: {value}\n")

    print(f"分析結果已保存到 {filename}")



