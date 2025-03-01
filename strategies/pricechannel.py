import yfinance as yf
import pandas as pd
import numpy as np

def run(stock_symbol, initial_capital, period=20):
    # 獲取最近 3 個月數據
    data = yf.download(stock_symbol, period="3mo")
    
    if data.empty:
        return "No data available for the selected stock."
    
    required_columns = ['High', 'Low', 'Close']
    if not all(col in data.columns for col in required_columns):
        return "Missing required data columns."
    
    # 計算 Price Channel 上下軌
    data['Upper Band'] = data['High'].rolling(window=period).max()
    data['Lower Band'] = data['Low'].rolling(window=period).min()
    
    # 確認技術指標是否有 NaN
    print(data[['Close', 'Upper Band', 'Lower Band']].isna().sum())  # 檢查缺失值

    # 填補 NaN 值
    data[['Upper Band', 'Lower Band']] = data[['Upper Band', 'Lower Band']].bfill().ffill()

    # 確保 data.columns 不是 MultiIndex
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = ['_'.join(col).strip() if col[1] else col[0] for col in data.columns]

    # 檢查欄位名稱
    print("Columns after renaming:", data.columns)

    # 找到 Close、Upper Band、Lower Band 對應的欄位名稱
    close_col = [col for col in data.columns if 'Close' in col][0]
    upper_band_col = 'Upper Band'
    lower_band_col = 'Lower Band'

    # 確保欄位對齊
    data[close_col], data[upper_band_col] = data[close_col].align(data[upper_band_col], axis=0, copy=False)
    data[close_col], data[lower_band_col] = data[close_col].align(data[lower_band_col], axis=0, copy=False)

    # 定義買賣信號
    data['Signal'] = 0
    data.loc[data[close_col] >= data[upper_band_col] * 0.99, 'Signal'] = 1  # 買入信號
    data.loc[data[close_col] <= data[lower_band_col] * 1.01, 'Signal'] = -1  # 賣出信號
    
    # 模擬交易系統
    capital = initial_capital
    position = 0
    trade_log = []
    peak_capital = initial_capital
    
    for i in range(len(data)):
        price = float(data[close_col].iloc[i])
        signal = int(data['Signal'].iloc[i])
        
        if signal == 1 and capital >= price:
            position = capital // price
            capital -= position * price
            trade_log.append({'type': 'buy', 'price': price, 'shares': position, 'date': data.index[i]})
        
        elif signal == -1 and position > 0:
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
    
    # 修正 profit_factor 計算，避免除以零
    buy_total = sum(t['price'] * t['shares'] for t in trade_log if t['type'] == 'buy')
    sell_total = sum(t['price'] * t['shares'] for t in trade_log if t['type'] == 'sell')
    profit_factor = (sell_total / buy_total) if buy_total > 0 else 0

    avg_pl = net_profit / total_trades if total_trades > 0 else 0
    
    # 計算平均持有K線數
    hold_days = [((trade_log[i]['date'] - trade_log[i-1]['date']).days) for i in range(1, len(trade_log), 2)]
    avg_k_lines = np.mean(hold_days) if hold_days else 0
    
    # 回傳結果
    result = {
        'net_profit': round(net_profit, 2),
        'max_drawdown': round(max_drawdown, 2),
        'total_trades': total_trades,
        'win_rate': round(win_rate, 2),
        'profit_factor': round(profit_factor, 2),
        'avg_pl': round(avg_pl, 2),
        'avg_k_lines': round(avg_k_lines, 2)
    }
    
    # 儲存結果到 TXT
    save_analysis_to_txt(result, data, close_col)
    
    return result

def save_analysis_to_txt(result, data, close_col):
    filename = "analysis_results.txt"
    
    with open(filename, "w", encoding="utf-8") as f:
        # 寫入 Price Channel Analysis
        f.write("--- Price Channel Analysis ---\n")
        f.write("Price        Close        Upper Band       Lower Band Signal\n")
        f.write("Ticker                                \n")
        f.write("Date                                \n")
        
        if 'Upper Band' in data.columns and 'Lower Band' in data.columns and 'Signal' in data.columns:
            f.write(data[[close_col, 'Upper Band', 'Lower Band', 'Signal']].tail(10).to_string() + "\n\n")
        else:
            f.write("Data columns missing for analysis.\n\n")
        
        # 寫入 Performance Summary
        f.write("--- Performance Summary ---\n")
        for key, value in result.items():
            f.write(f"{key}: {value}\n")
    
    print(f"分析結果已儲存至 {filename}")
