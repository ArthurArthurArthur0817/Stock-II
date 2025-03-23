import yfinance as yf
import talib
import pandas as pd
import numpy as np

def run(stock_symbol, initial_capital, acceleration=0.02, maximum=0.2):
    print(f"\n🚀 開始 SAR 分析: {stock_symbol} (資金: {initial_capital})")

    # 獲取最近 3 個月數據
    data = yf.download(stock_symbol, period="3mo", auto_adjust=False)

    if data.empty:
        return "No data available for the selected stock."

    # 檢查 MultiIndex 問題，確保欄位名稱正確
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [col[0] for col in data.columns]  # 取第一層索引名稱

    # 確保數據包含 High、Low、Close 欄位
    required_columns = {'High', 'Low', 'Close'}
    if not required_columns.issubset(data.columns):
        return f"Missing required columns: {required_columns - set(data.columns)}"

    # 計算 SAR
    data['SAR'] = talib.SAR(data['High'].values, data['Low'].values, acceleration=acceleration, maximum=maximum)
    data.dropna(inplace=True)

    # 定義買賣信號
    data['Signal'] = 0
    data.loc[data['SAR'] < data['Close'], 'Signal'] = 1  # 買入信號
    data.loc[data['SAR'] > data['Close'], 'Signal'] = -1  # 賣出信號

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
        'latest_SAR': round(data['SAR'].iloc[-1], 2),
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
        # SAR Analysis
        f.write("--- SAR Analysis ---\n")
        f.write(f"Stock: {stock_symbol}\n")
        f.write("Price        Close        SAR Signal\n")
        f.write("Date                                \n")

        # 確保 'SAR' 和 'Signal' 欄位存在
        if 'SAR' in data.columns and 'Signal' in data.columns:
            f.write(data[['Close', 'SAR', 'Signal']].tail(10).to_string() + "\n\n")
        else:
            f.write("SAR or Signal data is missing.\n\n")

        # Performance Summary
        f.write("--- Performance Summary ---\n")
        for key, value in result.items():
            f.write(f"{key}: {value}\n")

    print(f"📂 分析結果已儲存至 {filename}")

# ✅ 可調整輸入
if __name__ == "__main__":
    stock_ticker = input("請輸入股票代號 (例如 2330.TW): ")
    initial_capital = float(input("請輸入初始資金 (例如 100000): "))

    sar_result = run(stock_ticker, initial_capital)
    print("\n📈 最終結果:", sar_result)
