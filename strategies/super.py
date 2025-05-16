import yfinance as yf
import talib
import pandas as pd
import numpy as np

def run(stock_symbol, initial_capital, atr_period=14, multiplier=3):
    print(f"\n🚀 開始 Super Trend 分析: {stock_symbol} (資金: {initial_capital})")

    # 獲取最近 3 個月數據
    print("\n📡 正在獲取資料...")
    data = yf.download(stock_symbol, period="3mo", auto_adjust=False)
    
    if data.empty:
        return "No data available for the selected stock."
    
    print("\n✅ 資料已獲取 (前5行):")
    print(data.head())

    # 檢查 MultiIndex 問題，確保欄位名稱正確
    if isinstance(data.columns, pd.MultiIndex):
        print("\n🔧 發現多層索引，正在進行修正...")
        data.columns = [col[0] for col in data.columns]  # 取第一層索引名稱

    # 確保數據包含 High、Low、Close 欄位
    required_columns = {'High', 'Low', 'Close'}
    if not required_columns.issubset(data.columns):
        return f"Missing required columns: {required_columns - set(data.columns)}"

    # 計算 ATR
    print("\n📊 正在計算 ATR...")
    data['ATR'] = talib.ATR(data['High'].values, data['Low'].values, data['Close'].values, timeperiod=atr_period)
    
    print("\n✅ ATR 計算完成，最新的 5 筆資料:")
    print(data[['Close', 'ATR']].tail(5))

    # 計算 Super Trend
    print("\n📊 正在計算 Super Trend...")
    data['Upper Band'] = ((data['High'] + data['Low']) / 2) + (multiplier * data['ATR'])
    data['Lower Band'] = ((data['High'] + data['Low']) / 2) - (multiplier * data['ATR'])

    print("\n✅ 計算 Upper Band 和 Lower Band 完成，最新的 5 筆資料:")
    print(data[['Upper Band', 'Lower Band']].tail(5))

    # 初始化 Super Trend 和 Signal 欄位
    data['Super Trend'] = np.nan
    data['Signal'] = 0

    # 使用 iloc 來避免時間戳的加減問題
    for i in range(1, len(data)):  # 從第二行開始計算，第一行已經初始化
        prev_st = data.iloc[i - 1]['Super Trend']
        current_upper = data.iloc[i]['Upper Band']
        current_lower = data.iloc[i]['Lower Band']
        close_price = data.iloc[i]['Close']

        # 根據 Super Trend 計算
        if prev_st == data.iloc[i - 1]['Upper Band']:  # 如果前一天的 Super Trend 是上軌道
            data.loc[data.index[i], 'Super Trend'] = current_upper if close_price > prev_st else current_lower
        else:  # 如果前一天的 Super Trend 是下軌道
            data.loc[data.index[i], 'Super Trend'] = current_lower if close_price < prev_st else current_upper

        # 設定交易信號
        data.loc[data.index[i], 'Signal'] = 1 if close_price > data.loc[data.index[i], 'Super Trend'] else -1

    print("\n✅ Super Trend 計算完成，最新的 5 筆資料:")
    print(data[['Close', 'Super Trend', 'Signal']].tail(5))

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
        'latest_Super_Trend': round(data['Super Trend'].iloc[-1], 2),
        'net_profit': round(net_profit, 2),
        'max_drawdown': round(max_drawdown, 2),
        'total_trades': total_trades,
        'win_rate': round(win_rate, 2),
        'profit_factor': round(profit_factor, 2),
        'avg_pl': round(avg_pl, 2),
        'avg_k_lines': round(avg_k_lines, 2)
    }

    # 儲存結果到 TXT
    save_analysis_to_txt(stock_symbol, result, data)

    return result

def save_analysis_to_txt(stock_symbol, result, data):
    filename = "analysis_results.txt"

    with open(filename, "w", encoding="utf-8") as f:
        # Super Trend Analysis
        f.write("--- Super Trend Analysis ---\n")
        f.write(f"Stock: {stock_symbol}\n")
        f.write("Date         Close        Super Trend   Signal\n")
        
        # 儲存最新的10筆數據
        f.write(data[['Close', 'Super Trend', 'Signal']].tail(10).to_string() + "\n\n")

        # Performance Summary
        f.write("--- Performance Summary ---\n")
        for key, value in result.items():
            f.write(f"{key}: {value}\n")

    print(f"📂 分析結果已儲存至 {filename}")

# ✅ 可調整輸入
if __name__ == "__main__":
    stock_ticker = input("請輸入股票代號 (例如 2330.TW): ")
    initial_capital = float(input("請輸入初始資金 (例如 100000): "))

    result = run(stock_ticker, initial_capital)
    print("\n📈 最終結果:", result)
