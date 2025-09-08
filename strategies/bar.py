import yfinance as yf
import pandas as pd
import numpy as np

def run(stock_symbol, initial_capital):
    print("\n=== [Step 1] 下載資料 ===")
    data = yf.download(stock_symbol, period="1y")

    # ✅ 自動處理 MultiIndex 欄位
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.droplevel(1)

    print(data.head())
    print("資料型別：", type(data))
    print("欄位：", data.columns.tolist())

    if data.empty:
        return "No data available for the selected stock."

    # === [Step 2] 產生交易訊號 (BarUpDn 策略) ===
    data['Signal'] = 0
    data.loc[data['Close'] > data['Open'], 'Signal'] = 1   # 上漲紅K → 買進
    data.loc[data['Close'] < data['Open'], 'Signal'] = -1  # 下跌黑K → 賣出

    print("\n=== [Step 2] 加入 Signal 後的資料 ===")
    print(data.head(10))
    print("Signal 欄位型別：", data['Signal'].dtype)

    # === [Step 3] 模擬交易 ===
    print("\n=== [Step 3] 開始模擬交易 ===")
    capital = initial_capital
    position = 0
    trade_log = []
    peak_capital = initial_capital

    col_close = data.columns.get_loc("Close")
    col_signal = data.columns.get_loc("Signal")

    for i in range(len(data)):
        price = float(data.iat[i, col_close])      # ✅ 正確取 Close
        signal = int(data.iat[i, col_signal])      # ✅ 正確取 Signal

        if signal == 1 and capital >= price:  # 買入
            position = capital // price
            capital -= position * price
            trade_log.append({'type': 'buy', 'price': price, 'shares': position, 'date': data.index[i]})

        elif signal == -1 and position > 0:  # 賣出
            capital += position * price
            trade_log.append({'type': 'sell', 'price': price, 'shares': position, 'date': data.index[i]})
            position = 0

        peak_capital = max(peak_capital, capital)

    # === [Step 4] 計算績效指標 ===
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

    result = {
        'net_profit(淨利潤)': round(net_profit, 2),
        'max_drawdown(最大回撤)': round(max_drawdown, 2),
        'total_trades(總交易次數)': total_trades,
        'win_rate(勝率)': round(win_rate, 2),
        'profit_factor(獲利因子)': round(profit_factor, 2),
        'avg_pl(平均盈虧)': round(avg_pl, 2),
        'avg_k_lines(平均 K 線數)': round(avg_k_lines, 2)
    }

    # === [Step 5] 存檔 TXT ===
    save_analysis_to_txt_barupdn(result, data)

    return result


def save_analysis_to_txt_barupdn(result, data):
    filename = "analysis_results.txt"

    with open(filename, "w", encoding="utf-8") as f:
        f.write("--- BarUpDn Analysis ---\n")
        f.write("Date\tClose\tHigh\tLow\tOpen\tSignal\n")
        for i in range(len(data)):
            f.write(f"{data.index[i].date()}\t"
                    f"{float(data.iat[i, data.columns.get_loc('Close')]):.2f}\t"
                    f"{float(data.iat[i, data.columns.get_loc('High')]):.2f}\t"
                    f"{float(data.iat[i, data.columns.get_loc('Low')]):.2f}\t"
                    f"{float(data.iat[i, data.columns.get_loc('Open')]):.2f}\t"
                    f"{int(data.iat[i, data.columns.get_loc('Signal')])}\n")

        f.write("\n--- Performance Summary ---\n")
        for key, value in result.items():
            f.write(f"{key}: {value}\n")

    print(f"分析結果已保存至 {filename}")
