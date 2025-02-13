'''本金:100000 Signal觸發條件較嚴格 輸出結果皆為0
import yfinance as yf
import pandas as pd
import numpy as np

def fetch_and_analyze_price_channel(stock_ticker, start_date, end_date, initial_capital=100000, period=20):
    # 抓取股票數據
    data = yf.download(stock_ticker, start=start_date, end=end_date, group_by="ticker")
    
    if isinstance(data.columns, pd.MultiIndex):
        print("Detected multi-level columns, flattening...")
        data.columns = data.columns.droplevel(0)

    required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    if not all(col in data.columns for col in required_columns):
        print(f"Error: Missing required columns. Available columns: {list(data.columns)}")
        return None

    data = data[required_columns]
    
    # 計算 Price Channel 指標
    data['Upper Band'] = data['High'].rolling(window=period).max()
    data['Lower Band'] = data['Low'].rolling(window=period).min()
    data[['Upper Band', 'Lower Band']] = data[['Upper Band', 'Lower Band']].bfill()
    
    # 訊號定義
    data['Signal'] = 0
    data.loc[data['Close'] > data['Upper Band'], 'Signal'] = 1   # 突破上軌買入
    data.loc[data['Close'] < data['Lower Band'], 'Signal'] = -1  # 跌破下軌賣出
    
    # 交易模擬變數
    capital = initial_capital  # 初始資金
    position = 0  # 持倉數量
    trade_log = []  # 記錄交易
    peak_capital = initial_capital  # 最高資本（計算回撤用）
    
    for i in range(len(data)):
        price = float(data['Close'].iloc[i])
        signal = int(data['Signal'].iloc[i])
        
        if signal == 1 and capital >= price:  # 買入
            position = capital // price
            capital -= position * price
            trade_log.append({'type': 'buy', 'price': price, 'shares': position, 'date': data.index[i]})
        
        elif signal == -1 and position > 0:  # 賣出
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
    
    hold_days = [((trade_log[i]['date'] - trade_log[i-1]['date']).days) for i in range(1, len(trade_log), 2)]
    avg_k_lines = np.mean(hold_days) if hold_days else 0
    
    # 顯示結果
    print("\n--- Price Channel Analysis ---")
    print(data[['Close', 'Upper Band', 'Lower Band', 'Signal']].tail(10))
    
    print("\n--- Performance Summary ---")
    print(f"淨利: {net_profit:.2f}")
    print(f"最大資本回撤: {max_drawdown:.2f}%")
    print(f"總交易次數: {total_trades}")
    print(f"勝率: {win_rate:.2f}%")
    print(f"獲利因子: {profit_factor:.2f}")
    print(f"平均盈虧: {avg_pl:.2f}")
    print(f"交易的平均K線數: {avg_k_lines:.2f}")
    
    return data

# 使用範例
if __name__ == "__main__":
    stock_ticker = "2330.TW"
    start_date = "2024-01-01"
    end_date = "2024-12-31"
    initial_capital = 100000
    
    fetch_and_analyze_price_channel(stock_ticker, start_date, end_date, initial_capital)
'''

# 提高本金至500000 且放寬Signal觸發條件

import yfinance as yf
import pandas as pd
import numpy as np

def fetch_and_analyze_price_channel(stock_ticker, start_date, end_date, initial_capital=500000, period=20):
    # 抓取股票數據
    data = yf.download(stock_ticker, start=start_date, end=end_date, group_by="ticker")

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.droplevel(0)  # 處理多層索引

    required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    if not all(col in data.columns for col in required_columns):
        print(f"Error: 缺少必要欄位: {list(data.columns)}")
        return None

    data = data[required_columns]

    # 計算 Price Channel 上下軌
    data['Upper Band'] = data['High'].rolling(window=period).max()
    data['Lower Band'] = data['Low'].rolling(window=period).min()
    data[['Upper Band', 'Lower Band']] = data[['Upper Band', 'Lower Band']].bfill()

    # 訊號產生 (放寬觸發條件)
    data['Signal'] = 0
    data.loc[data['Close'] >= data['Upper Band'] * 0.99, 'Signal'] = 1  # 買入
    data.loc[data['Close'] <= data['Lower Band'] * 1.01, 'Signal'] = -1  # 賣出

    # 交易模擬
    capital = initial_capital  # 初始資金
    position = 0  # 持倉數量
    trade_log = []  # 記錄交易
    peak_capital = initial_capital  # 追蹤最高資金

    for i in range(len(data)):
        price = float(data['Close'].iloc[i])
        signal = int(data['Signal'].iloc[i])

        if signal == 1 and capital >= price:  # 買入條件
            shares_to_buy = capital // price  # 買得起幾股
            capital -= shares_to_buy * price
            position += shares_to_buy
            trade_log.append({'type': 'buy', 'price': price, 'shares': shares_to_buy, 'date': data.index[i]})

        elif signal == -1 and position > 0:  # 賣出條件
            capital += position * price  # 賣出後獲得的資金
            trade_log.append({'type': 'sell', 'price': price, 'shares': position, 'date': data.index[i]})
            position = 0  # 清空持倉

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
    print("\n--- Price Channel Analysis ---")
    print(data.loc["2024-12-01":"2024-12-31", ['Close', 'Upper Band', 'Lower Band', 'Signal']])

    print("\n--- Performance Summary ---")
    print(f"淨利: {net_profit:.2f}")
    print(f"最大資本回撤: {max_drawdown:.2f}%")
    print(f"總交易次數: {total_trades}")
    print(f"勝率: {win_rate:.2f}%")
    print(f"獲利因子: {profit_factor:.2f}")
    print(f"平均盈虧: {avg_pl:.2f}")
    print(f"交易的平均K線數: {avg_k_lines:.2f}")

    return data

# 參數設定
stock_ticker = '2330.TW'
start_date = '2024-01-01'
end_date = '2024-12-31'
initial_capital = 500000  # 增加初始資金

result = fetch_and_analyze_price_channel(stock_ticker, start_date, end_date, initial_capital)
