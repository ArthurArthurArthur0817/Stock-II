import yfinance as yf
import talib
import pandas as pd
import numpy as np

def run(stock_symbol, initial_capital, window=5, num_std_dev=1):
    # 獲取最近 3 個月數據
    data = yf.download(stock_symbol, period="3mo")
    
    if data.empty or 'Close' not in data.columns:
        return "No data available for the selected stock."
    
    close_prices = data[('Close', stock_symbol)]

    if close_prices.isna().any():
        print("數據中包含缺失值，將自動刪除 NaN 行。")
        data = data.dropna(subset=['Close'])
    
    if data.empty:
        print(f"找不到股票代碼 {stock_ticker} 的數據，請確認代碼或日期是否正確。")
        return

    # 計算布林通道
    upper_band, middle_band, lower_band = talib.BBANDS(
        close_prices, timeperiod=window, nbdevup=num_std_dev, nbdevdn=num_std_dev, matype=0
    )

    # 將布林帶數據加入到 DataFrame 中
    data[('Moving Average', stock_symbol)] = middle_band
    data[('Upper Band', stock_symbol)] = upper_band
    data[('Lower Band', stock_symbol)] = lower_band

    # 刪除 NaN 行
    data = data[['Close', 'Moving Average', 'Upper Band', 'Lower Band']].dropna()

     # 設定買賣信號
    data['Signal'] = np.where(data[('Close', stock_symbol)] < data[('Lower Band', stock_symbol)], 1, 0)  # 買入信號
    data['Signal'] = np.where(data[('Close', stock_symbol)] > data[('Upper Band', stock_symbol)], -1, data['Signal'])  # 賣出信號


    # 模擬交易系統
    capital = initial_capital
    position = 0
    trade_log = []
    peak_capital = initial_capital
    
    for i in range(len(data)):
        price = float(data['Close'].iloc[i])
        signal = int(data['Signal'].iloc[i])

        if signal == 1 and capital >= price:  # 買入條件
            position = capital // price
            capital -= position * price
            trade_log.append({'type': 'buy', 'price': price, 'shares': position, 'date': data.index[i]})
        
        elif signal == -1 and position > 0:  # 賣出條件
            capital += position * price
            trade_log.append({'type': 'sell', 'price': price, 'shares': position, 'date': data.index[i]})
            position = 0
        
        peak_capital = max(peak_capital, capital)

    # 計算績效指標
    net_profit = capital - initial_capital
    max_drawdown = (peak_capital - capital) / peak_capital * 100 if peak_capital > 0 else 0
    total_trades = len(trade_log) // 2
    wins = sum(1 for i in range(1, len(trade_log), 2) if trade_log[i]['price'] > trade_log[i-1]['price'])
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
    profit_factor = (sum(t['price'] * t['shares'] for t in trade_log if t['type'] == 'sell') /
                     sum(t['price'] * t['shares'] for t in trade_log if t['type'] == 'buy')) if total_trades > 0 else 0
    avg_pl = net_profit / total_trades if total_trades > 0 else 0
    
    # 計算平均持有K線數
    hold_days = [((trade_log[i]['date'] - trade_log[i-1]['date']).days) for i in range(1, len(trade_log), 2)]
    avg_k_lines = np.mean(hold_days) if hold_days else 0

    # 回傳結果
    result = {
        'latest_Close': round(data['Close'].iloc[-1].iloc[0], 2),
        'latest_MA': round(data['Moving Average'].iloc[-1].iloc[0], 2),
        'latest_Upper_Band': round(data['Upper Band'].iloc[-1].iloc[0], 2),
        'latest_Lower_Band': round(data['Lower Band'].iloc[-1].iloc[0], 2),
        'net_profit': round(net_profit, 2),
        'max_drawdown': round(max_drawdown, 2),
        'total_trades': total_trades,
        'win_rate': round(win_rate, 2),
        'profit_factor': round(profit_factor, 2),
        'avg_pl': round(avg_pl, 2),
        'avg_k_lines': round(avg_k_lines, 2)
    }

    # 儲存結果到 TXT
    save_analysis_to_txt(result, data, stock_symbol)

    return result

def save_analysis_to_txt(result, data, stock_symbol):
    filename = "analysis_results.txt"

    with open(filename, "w", encoding="utf-8") as f:
        # 寫入布林通道分析
        f.write("--- Bollinger Bands Analysis ---\n")
        f.write("Price        Close    MA    UpperBand    LowerBand    Signal\n")
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

        # 寫入績效總結
        f.write("--- Performance Summary ---\n")
        for key, value in result.items():
            f.write(f"{key}: {value}\n")

    print(f"分析結果已儲存至 {filename}")
