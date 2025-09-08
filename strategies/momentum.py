import yfinance as yf
import talib
import pandas as pd
import numpy as np


def run(stock_symbol, initial_capital, momentum_period=14, buy_threshold=2, sell_threshold=-2):
    # 抓取股票數據
    data = yf.download(stock_symbol, period="3y")
    
    if data.empty:
        return "No data available for the selected stock."
    
    # 清理缺失值
    data.dropna(inplace=True)
    close_prices = data['Close'].squeeze()
    
    # 計算 Momentum 指標
    data['Momentum'] = talib.MOM(close_prices.values, timeperiod=momentum_period).astype(float)
    data.dropna(inplace=True)
    
    # 定義買賣信號
    data['Signal'] = 0
    data.loc[data['Momentum'] > buy_threshold, 'Signal'] = 1    # 買入信號
    data.loc[data['Momentum'] < sell_threshold, 'Signal'] = -1  # 賣出信號
    
    # 模擬交易系統
    capital = initial_capital
    position = 0
    trade_log = []
    equity_curve = []
    peak = initial_capital
    
    for i in range(len(data)):
        price = float(data['Close'].iloc[i])
        signal = int(data['Signal'].iloc[i])
        
        # 買入條件
        if signal == 1 and capital >= price:
            position = capital // price
            capital -= position * price
            trade_log.append({'type': 'buy', 'price': price, 'shares': position, 'date': data.index[i]})
        
        # 賣出條件
        elif signal == -1 and position > 0:
            capital += position * price
            trade_log.append({'type': 'sell', 'price': price, 'shares': position, 'date': data.index[i]})
            position = 0
        
        # 當前總資產（資金 + 未平倉市值）
        equity = capital + position * price
        equity_curve.append(equity)
        peak = max(peak, equity)
    
    # 如果最後還有持倉，計算最終市值
    final_value = capital + position * float(data['Close'].iloc[-1])
    
    # 計算績效指標
    net_profit = final_value - initial_capital
    
    # 最大回撤
    if equity_curve:
        drawdowns = [(peak - eq) / peak for eq in equity_curve]
        max_drawdown = max(drawdowns) * 100
    else:
        max_drawdown = 0
    
    # 計算單次交易盈虧
    profits = []
    for i in range(1, len(trade_log), 2):  # 成對買賣
        buy = trade_log[i - 1]
        sell = trade_log[i]
        pnl = (sell['price'] - buy['price']) * buy['shares']
        profits.append(pnl)
    
    total_trades = len(profits)
    wins = sum(1 for p in profits if p > 0)
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
    
    gross_profit = sum(p for p in profits if p > 0)
    gross_loss = abs(sum(p for p in profits if p < 0))
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float('inf')
    
    avg_pl = float(np.mean(profits)) if profits else 0
    
    # 平均持倉天數
    hold_days = [((trade_log[i]['date'] - trade_log[i - 1]['date']).days) for i in range(1, len(trade_log), 2)]
    avg_k_lines = float(np.mean(hold_days)) if hold_days else 0
    
    # 回傳結果
    result = {
        'latest_Momentum': round(float(data['Momentum'].iloc[-1]), 2),
        'net_profit': round(float(net_profit), 2),
        'max_drawdown': round(float(max_drawdown), 2),
        'total_trades': total_trades,
        'win_rate': round(float(win_rate), 2),
        'profit_factor': round(float(profit_factor), 2) if profit_factor != float('inf') else '∞',
        'avg_pl': round(float(avg_pl), 2),
        'avg_k_lines': round(float(avg_k_lines), 2)
    }
    
    save_analysis_to_txt(result, data)
    return result


def save_analysis_to_txt(result, data):
    filename = "analysis_results.txt"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write("--- Momentum Analysis ---\n")
        f.write("Price        Close        Momentum Signal\n")
        f.write("Ticker                       \n")
        f.write("Date                                \n")
        
        if 'Momentum' in data.columns and 'Signal' in data.columns:
            f.write(data[['Close', 'Momentum', 'Signal']].tail(10).to_string() + "\n\n")
        else:
            f.write("Momentum or Signal data is missing.\n\n")
        
        f.write("--- Performance Summary ---\n")
        for key, value in result.items():
            f.write(f"{key}: {value}\n")
    
    print(f"分析結果已儲存至 {filename}")
