import yfinance as yf
import pandas as pd
import numpy as np

def run(stock_symbol, initial_capital):
    # 獲取最近 3 個月數據
    data = yf.download(stock_symbol, period="3mo")
    
    if data.empty:
        return "No data available for the selected stock."
    
    close_prices = data['Close'].squeeze()
    
    # 計算每日收盤價變化
    data['Change'] = data['Close'].diff()
    
    # 設定買入、賣出、不變的信號
    data['Signal'] = 0
    data.loc[data['Change'] > 0, 'Signal'] = 1   # 當天價格上漲，買入
    data.loc[data['Change'] < 0, 'Signal'] = -1  # 當天價格下跌，賣出
    
    # 初始化交易變數
    capital = initial_capital  # 初始資金
    position = 0  # 持倉數量
    trade_log = []  # 記錄交易
    peak_capital = initial_capital  # 記錄最高資金（計算回撤）
    
    for i in range(len(data)):
        price = float(data['Close'].iloc[i])  # 確保為單一數值
        signal = int(data['Signal'].iloc[i])  # 確保為單一數值

        if signal == 1 and capital >= price:  # 買入條件
            position = capital // price  # 買入的股數
            capital -= position * price
            trade_log.append({'type': 'buy', 'price': price, 'shares': position, 'date': data.index[i]})

        elif signal == -1 and position > 0:  # 賣出條件
            capital += position * price  # 賣出獲得的資金
            trade_log.append({'type': 'sell', 'price': price, 'shares': position, 'date': data.index[i]})
            position = 0  # 清空持倉
        
        # 記錄最高資本值（計算回撤用）
        peak_capital = max(peak_capital, capital)
    
    # 計算績效指標
    net_profit = capital - initial_capital
    max_drawdown = (peak_capital - capital) / peak_capital * 100 if peak_capital > 0 else 0
    total_trades = len(trade_log) // 2  # 只計算完整的買賣循環
    wins = sum(1 for i in range(1, len(trade_log), 2) if trade_log[i]['price'] > trade_log[i-1]['price'])
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
    profit_factor = (sum(t['price'] * t['shares'] for t in trade_log if t['type'] == 'sell') /
                     sum(t['price'] * t['shares'] for t in trade_log if t['type'] == 'buy')) if total_trades > 0 else 0
    avg_pl = net_profit / total_trades if total_trades > 0 else 0
    
    # 計算平均持有 K 線數
    hold_days = [((trade_log[i]['date'] - trade_log[i-1]['date']).days) for i in range(1, len(trade_log), 2)]
    avg_k_lines = np.mean(hold_days) if hold_days else 0
    
    # 將結果存成字典
    result = {
        'net_profit': round(net_profit, 2),
        'max_drawdown': round(max_drawdown, 2),
        'total_trades': total_trades,
        'win_rate': round(win_rate, 2),
        'profit_factor': round(profit_factor, 2),
        'avg_pl': round(avg_pl, 2),
        'avg_k_lines': round(avg_k_lines, 2)
    }

    # 儲存結果到 TXT 檔案
    save_analysis_to_txt(result, data)

    return result

def save_analysis_to_txt(result, data):
    filename = "analysis_results.txt"

    with open(filename, "w", encoding="utf-8") as f:
        # 寫入策略分析
        f.write("--- Greedy Strategy Analysis ---\n")
        f.write("Price       Close   Change   Signal\n")
        f.write("Ticker                             \n")
        f.write("Date                                \n")
        
        # 確保 'Change' 和 'Signal' 欄位存在
        if 'Change' in data.columns and 'Signal' in data.columns:
            f.write(data[['Close', 'Change', 'Signal']].tail(10).to_string() + "\n\n")
        else:
            f.write("Change or Signal data is missing.\n\n")

        # 寫入績效總結
        f.write("--- Performance Summary ---\n")
        for key, value in result.items():
            f.write(f"{key}: {value}\n")

    print(f"分析結果已儲存至 {filename}")