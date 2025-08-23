import os
import pandas as pd
import ta
import mplfinance as mpf
import time

DATA_DIR = './industry_data'
STATIC_DIR = 'static'

STOCK_LIST = [
    ('2610', '華航'),
    ('5678', '台達電'),
]  # 可擴充
EVENTS = {
    '2610': [
        ('2020/01/10', '法說會'),
        ('2020/03/19', '臺灣全面禁止外籍人士入境'),
        ('2020/05/19', '疫情爆發，臺灣進入三級警戒')
    ],
    '5678': [
        ('2020/03/01', '高層異動'),
        ('2020/04/01', '股東大會')
    ]
}


class TradingIndustry:
    def __init__(self, initial_balance=100000):
        self.balance = initial_balance
        self.held_stocks = 0

    def buy(self, price):
        if self.balance < price:
            return False
        self.balance -= price
        self.held_stocks += 1
        return True

    def sell(self, price):
        if self.held_stocks <= 0:
            return False
        self.balance += price
        self.held_stocks -= 1
        return True

    def close_position(self, price):
        if self.held_stocks <= 0:
            return False
        self.balance += price * self.held_stocks
        self.held_stocks = 0
        return True

    def get_balance(self):
        return self.balance

    def get_held_stocks(self):
        return self.held_stocks

# 全域變數實例（示範用）
trading_industry = TradingIndustry()


def get_available_stocks():
    return STOCK_LIST

def indusrty_fetch_stock_data(stock_code):
    csv_path = os.path.join(DATA_DIR, f"{stock_code}.csv")
    return os.path.exists(csv_path)

def get_stock_dataframe(stock_code):
    csv_path = os.path.join(DATA_DIR, f"{stock_code}.csv")
    # 讀取時指定日期欄位，確保是大寫 Date，並把它當作索引
    df = pd.read_csv(csv_path, parse_dates=['Date'])
    return df

def compute_indicators(df):
    df = df.copy()
    
    # RSI
    df['rsi'] = ta.momentum.RSIIndicator(close=df['Close'], window=14).rsi()
    
    # MACD
    macd_indicator = ta.trend.MACD(close=df['Close'])
    df['macd'] = macd_indicator.macd()
    
    # ADX 與 DI
    adx_indicator = ta.trend.ADXIndicator(high=df['High'], low=df['Low'], close=df['Close'], window=14)
    df['adx'] = adx_indicator.adx()
    df['plus_di'] = adx_indicator.adx_pos()  # +DI
    df['minus_di'] = adx_indicator.adx_neg() # -DI
    
    # 處理 NaN 值
# 假設你已經有 macd_indicator = ta.trend.MACD(close=df['Close'])

    try:
        df['rsi'] = df['rsi'].bfill().ffill().fillna(50.0)
        df['macd'] = df['macd'].bfill().ffill().fillna(0.0)
        df['macd_signal'] = macd_indicator.macd_signal().bfill().ffill().fillna(0.0)  # 新增
        df['adx'] = df['adx'].bfill().ffill().fillna(25.0)
        df['plus_di'] = df['plus_di'].bfill().ffill().fillna(25.0)
        df['minus_di'] = df['minus_di'].bfill().ffill().fillna(25.0)
    except:
        df['rsi'] = df['rsi'].fillna(method='bfill').fillna(method='ffill').fillna(50.0)
        df['macd'] = df['macd'].fillna(method='bfill').fillna(method='ffill').fillna(0.0)
        df['macd_signal'] = macd_indicator.macd_signal().fillna(method='bfill').fillna(method='ffill').fillna(0.0)  # 新增
        df['adx'] = df['adx'].fillna(method='bfill').fillna(method='ffill').fillna(25.0)
        df['plus_di'] = df['plus_di'].fillna(method='bfill').fillna(method='ffill').fillna(25.0)
        df['minus_di'] = df['minus_di'].fillna(method='bfill').fillna(method='ffill').fillna(25.0)

    return df


def get_safe_start_index(df):
    """計算安全的開始索引，確保技術指標有意義的值"""
    # MACD 需要最多天數（26天慢線 + 9天信號線 = 35天）
    # 但我們保守一點，用 30 天
    safe_start = min(30, len(df) - 10)  # 至少保留10天供模擬
    return max(0, safe_start)

def detect_upcoming_event(stock_code, df, current_index):
    current_date = df.iloc[current_index]['Date']
    current_date = pd.to_datetime(current_date)
    
    messages = []
    for event_date_str, name in EVENTS.get(stock_code, []):
        event_date = pd.to_datetime(event_date_str)
        if 0 <= (event_date - current_date).days <= 10:
            messages.append(f"提醒：{name} 即將於 {event_date_str} 發生")
    return messages

def industry_plot_stock_data(stock_code, start_index):
    """繪製股票走勢圖"""
    csv_path = os.path.join(DATA_DIR, f'{stock_code}.csv')
    if not os.path.exists(csv_path):
        return None  # 檔案不存在

    df = pd.read_csv(csv_path, parse_dates=['Date'], index_col='Date')
    
    end_index = start_index + 10
    df_subset = df.iloc[start_index:end_index]
    
    if df_subset.empty:
        return None
    
    mc = mpf.make_marketcolors(up='r', down='g', inherit=True)
    s = mpf.make_mpf_style(base_mpf_style='yahoo', marketcolors=mc)

    kwargs = dict(type='candle', mav=(5, 20, 60), volume=True, figratio=(10, 8), figscale=0.75, style=s)
    
    static_path = os.path.join("static", f"{stock_code}_chart.png")  
    mpf.plot(df_subset, **kwargs, savefig=static_path)
    
    return static_path

def cleanup_old_plots(stock_code):
    """清理舊的圖片檔案，只保留最新的5個"""
    try:
        # 找出所有相關的圖片檔案
        plot_files = []
        for filename in os.listdir(STATIC_DIR):
            if filename.startswith(f"{stock_code}_") and filename.endswith('.png'):
                filepath = os.path.join(STATIC_DIR, filename)
                plot_files.append((filepath, os.path.getctime(filepath)))
        
        # 按建立時間排序，保留最新5個
        plot_files.sort(key=lambda x: x[1], reverse=True)
        
        # 刪除多餘的檔案
        for filepath, _ in plot_files[5:]:
            try:
                os.remove(filepath)
            except:
                pass  # 忽略刪除錯誤
    except:
        pass  # 忽略清理錯誤
    
