import yfinance as yf
import pandas as pd
import numpy as np

def fetch_and_analyze_greedy(stock_ticker, start_date, end_date, initial_capital=100000):
    # 抓取股票數據
    data = yf.download(stock_ticker, start=start_date, end=end_date)
    
    if data.empty:
        print(f"No data found for {stock_ticker}.")
        return
    
    # 確保 'Close' 欄位是 Series 類型
    close_prices = data['Close'].squeeze()
    
    # 計算每日收盤價變化
    data['Change'] = data['Close'].diff()
    
    # 定義買入、賣出、不變的信號
    data['Signal'] = 0
    data.loc[data['Change'] > 0, 'Signal'] = 1   # 當天價格上漲，買入
    data.loc[data['Change'] < 0, 'Signal'] = -1  # 當天價格下跌，賣出
    data.loc[data['Change'] == 0, 'Signal'] = 0  # 價格不變，保持不動
    
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
    
    # 計算平均持有K線數
    hold_days = [((trade_log[i]['date'] - trade_log[i-1]['date']).days) for i in range(1, len(trade_log), 2)]
    avg_k_lines = np.mean(hold_days) if hold_days else 0
    
    # 顯示結果
    print("\n--- Greedy Strategy Analysis ---")
    print(data[['Close', 'Change', 'Signal']].tail(10))  # 顯示最後10筆記錄
    
    print("\n--- Performance Summary ---")
    print(f"淨利: {net_profit:.2f}")
    print(f"最大資本回撤: {max_drawdown:.2f}%")
    print(f"總交易次數: {total_trades}")
    print(f"勝率: {win_rate:.2f}%")
    print(f"獲利因子: {profit_factor:.2f}")
    print(f"平均盈虧: {avg_pl:.2f}")
    print(f"交易的平均K線數: {avg_k_lines:.2f}")

# 使用範例
if __name__ == "__main__":
    stock_ticker = "2330.TW"
    start_date = "2024-01-01"
    end_date = "2024-09-30"
    initial_capital = 100000  # 初始資金

    fetch_and_analyze_greedy(stock_ticker, start_date, end_date, initial_capital)
