import yfinance as yf
import talib
import pandas as pd
import numpy as np

def run(stock_symbol, initial_capital, adx_period=14, threshold=18):
    # 获取最近 3 个月数据
    data = yf.download(stock_symbol, period="1y")

    if data.empty:
        return "No data available for the selected stock."

    high_prices = data['High'].squeeze()
    low_prices = data['Low'].squeeze()
    close_prices = data['Close'].squeeze()

    # 计算 ADX, +DI, -DI
    data['ADX'] = talib.ADX(high_prices, low_prices, close_prices, timeperiod=adx_period)
    data['+DI'] = talib.PLUS_DI(high_prices, low_prices, close_prices, timeperiod=adx_period)
    data['-DI'] = talib.MINUS_DI(high_prices, low_prices, close_prices, timeperiod=adx_period)

    # 处理空值
    #columns_needed = ['ADX', '+DI', '-DI']
    #existing_columns = [col for col in columns_needed if col in data.columns]

    '''
    if existing_columns:
        data.dropna(subset=existing_columns, inplace=True)   '''

    # 定义交易信号 (ADX > threshold 且 +DI > -DI 视为买入信号)
    data['Signal'] = 0
    data.loc[(data['ADX'] > threshold) & (data['+DI'] > data['-DI']), 'Signal'] = 1  # 买入信号
    data.loc[(data['ADX'] > threshold) & (data['+DI'] < data['-DI']), 'Signal'] = -1  # 卖出信号

    # 模拟交易系统
    capital = initial_capital
    position = 0
    trade_log = []
    peak_capital = initial_capital

    for i in range(len(data)):
        price = float(data['Close'].iloc[i])
        signal = int(data['Signal'].iloc[i])

        if signal == 1 and capital >= price:  # 买入条件
            position = capital // price
            capital -= position * price
            trade_log.append({'type': 'buy', 'price': price, 'shares': position, 'date': data.index[i]})

        elif signal == -1 and position > 0:  # 卖出条件
            capital += position * price
            trade_log.append({'type': 'sell', 'price': price, 'shares': position, 'date': data.index[i]})
            position = 0

        peak_capital = max(peak_capital, capital)

    # 计算绩效指标
    net_profit = capital - initial_capital
    max_drawdown = (peak_capital - capital) / peak_capital * 100 if peak_capital > 0 else 0
    total_trades = len(trade_log) // 2
    wins = sum(1 for i in range(1, len(trade_log), 2) if trade_log[i]['price'] > trade_log[i-1]['price'])
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
    profit_factor = (sum(t['price'] * t['shares'] for t in trade_log if t['type'] == 'sell') /
                     sum(t['price'] * t['shares'] for t in trade_log if t['type'] == 'buy')) if total_trades > 0 else 0
    avg_pl = net_profit / total_trades if total_trades > 0 else 0

    # 计算平均持有 K 线数
    hold_days = [((trade_log[i]['date'] - trade_log[i-1]['date']).days) for i in range(1, len(trade_log), 2)]
    avg_k_lines = np.mean(hold_days) if hold_days else 0

    # 结果
    result = {
        'latest_ADX(ADX指數)': round(data['ADX'].iloc[-1], 2),
        'net_profit(淨利潤)': round(net_profit, 2),
        'max_drawdown(最大回撤)': round(max_drawdown, 2),
        'total_trades(總交易次數)': total_trades,
        'win_rate(勝率)': round(win_rate, 2),
        'profit_factor(獲利因子)': round(profit_factor, 2),
        'avg_pl(平均盈虧)': round(avg_pl, 2),
        'avg_k_lines(平均 K 線數)': round(avg_k_lines, 2)
    }

    # 存入 TXT
    save_analysis_to_txt(result, data)

    return result

def save_analysis_to_txt(result, data):
    filename = "analysis_results.txt"

    with open(filename, "w", encoding="utf-8") as f:
        # 按照 date  adx  dI+  di- 格式写入
        f.write("--- ADX Analysis ---\n")
        f.write("Date\tADX\t+DI\t-DI\n")
        for i in range(len(data)):
            f.write(f"{data.index[i].date()}\t"
                    f"{data['ADX'].iloc[i]:.2f}\t"
                    f"{data['+DI'].iloc[i]:.2f}\t"
                    f"{data['-DI'].iloc[i]:.2f}\n")

        f.write("\n--- Performance Summary ---\n")
        for key, value in result.items():
            f.write(f"{key}: {value}\n")

    print(f"分析结果已保存至 {filename}")

