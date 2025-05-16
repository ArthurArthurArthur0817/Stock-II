import yfinance as yf
import pandas as pd
import talib
import numpy as np

# 設定顯示所有行
pd.set_option('display.max_rows', None)

def run(stock_symbol="2330.TW", initial_capital=100000, short_ma_period=5, long_ma_period=20):
    print(f"\n🚀 開始 MA 分析: {stock_symbol} (資金: {initial_capital})")

    # 下載最近 3 個月的數據
    data = yf.download(stock_symbol, period="3mo", auto_adjust=False)

    if data.empty:
        print("❌ No data available for the selected stock.")
        return

    print("\n📊 原始數據 (前5行):")
    print(data.head())  # 印出前 5 行原始數據

    # 檢查必要欄位是否存在
    required_columns = ['Close']
    for col in required_columns:
        if col not in data.columns:
            print(f"❌ 缺少必要欄位: {col}")
            return

    # **修正 Close 欄位格式**
    close_prices = data['Close'].values.squeeze()  # 確保是 1D 陣列
    print(f"\n🔍 Close 資料形狀: {close_prices.shape}")  # 應該是 (N,)

    # 計算短期與長期移動平均
    data['Short_MA'] = talib.SMA(close_prices, timeperiod=short_ma_period)
    data['Long_MA'] = talib.SMA(close_prices, timeperiod=long_ma_period)

    print("\n📈 計算 MA 後的數據 (前5行):")
    print(data[['Close', 'Short_MA', 'Long_MA']].head())

    # 移除 NaN 值
    data.dropna(inplace=True)

    # 定義買賣信號
    data['Signal'] = 0
    data.loc[data['Short_MA'] > data['Long_MA'], 'Signal'] = 1  # 短期MA上穿長期MA，買入信號
    data.loc[data['Short_MA'] <= data['Long_MA'], 'Signal'] = -1  # 短期MA下穿長期MA，賣出信號

    print("\n🔍 添加買賣信號 (前5行):")
    print(data[['Close', 'Short_MA', 'Long_MA', 'Signal']].head())

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
        'latest_Short_MA': round(data['Short_MA'].iloc[-1], 2),
        'latest_Long_MA': round(data['Long_MA'].iloc[-1], 2),
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
        # MA Analysis
        f.write("--- Moving Average Analysis ---\n")
        f.write(f"Stock: {stock_symbol}\n")
        f.write("Price        Close    Short_MA    Long_MA    Signal\n")
        f.write("Date                                       \n")

        # 確保 'Short_MA' 和 'Long_MA' 存在
        if 'Short_MA' in data.columns and 'Long_MA' in data.columns:
            f.write(data[['Close', 'Short_MA', 'Long_MA', 'Signal']].tail(10).to_string() + "\n\n")
        else:
            f.write("Short_MA or Long_MA data is missing.\n\n")

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
