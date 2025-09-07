import os
import pandas as pd
import ta
import mplfinance as mpf
import time

DATA_DIR = './industry_data'
STATIC_DIR = 'static'

STOCK_LIST = [
    ('2610', '華航'),
    ('2330', '台積電'),
]  # 可擴充
EVENTS = {
    '2610':  [
        # 2020 年
        ('2020/03/11', '世界衛生組織宣佈，新冠疫情已構成「全球大流行」'),
        ('2020/03/19', '臺灣全面禁止外籍人士入境'),
        ('2020/03/18', '董事會決議不發放股利'),
        ('2020/05/19', '疫情爆發，臺灣進入三級警戒'),
        ('2020/06/14', '中華航空202號班機在松山機場降落時發生設備故障，所幸無人傷亡'),
        ('2020/07/01', '中華航空宣布將裁員以應對疫情影響'),
        ('2020/08/15', '中華航空與長榮航空達成合作協議，共同應對疫情挑戰'),
        ('2020/10/01', '中華航空啟動貨運業務轉型計劃'),
        ('2020/11/15', '中華航空宣布將增設國際貨運航線'),
        ('2020/12/01', '中華航空獲得政府補助以維持營運'),

        # 2021 年
        ('2021/01/15', '中華航空宣布將進行機隊更新計劃'),
        ('2021/02/01', '中華航空啟動員工再培訓計劃'),
        ('2021/03/01', '中華航空與國際航空聯盟達成合作協議'),
        ('2021/04/01', '中華航空宣布將開設新航點'),
        ('2021/05/01', '中華航空推出新航班時刻表'),
        ('2021/06/01', '中華航空啟動數位轉型計劃'),
        ('2021/07/01', '中華航空與主要機場達成合作協議'),
        ('2021/08/01', '中華航空宣布將增加貨運航班'),
        ('2021/09/01', '中華航空推出新客艙服務'),
        ('2021/10/01', '中華航空啟動環境永續計劃'),
        ('2021/11/01', '中華航空與國際航空公司達成聯營協議'),
        ('2021/12/01', '中華航空宣布將進行機場設施升級'),

        # 2022 年
        ('2022/01/01', '中華航空推出新年優惠活動'),
        ('2022/02/01', '中華航空與旅遊業者達成合作協議'),
        ('2022/03/01', '中華航空啟動春季航季計劃'),
        ('2022/04/01', '中華航空與國際航空公司達成聯盟協議'),
        ('2022/05/01', '中華航空推出夏季航季計劃'),
        ('2022/06/01', '中華航空啟動員工健康促進計劃'),
        ('2022/07/01', '中華航空與主要機場達成合作協議'),
        ('2022/08/01', '中華航空宣布將增加國際航班'),
        ('2022/09/01', '中華航空推出秋季優惠活動'),
        ('2022/10/01', '中華航空啟動冬季航季計劃'),
        ('2022/11/01', '中華航空與旅遊業者達成合作協議'),
        ('2022/12/01', '中華航空推出聖誕節優惠活動'),

        # 股東會與股利發放
        ('2025/04/10', '董事會決議召開 2025 年股東常會'),
        ('2025/05/28', '2025 年股東常會召開'),
        ('2025/06/16', '公告現金股利配息基準日'),
        ('2025/07/16', '除息交易日'),
        ('2025/07/17', '最後過戶日'),
        ('2025/07/18', '停止過戶起始日期'),
        ('2025/07/22', '停止過戶截止日期'),
        ('2025/08/18', '現金股利發放日')
    ],
    '2330':  [
    # 2020
    ('2020-03-04', '5奈米進入量產'),
    ('2020-04-01', '5-奈米製程（N5）進入量產'),
    ('2020-05-14', '宣布斥資 120 億美元於美國亞利桑那州設立 5-奈米晶圓廠'),
    ('2020-06-09', '召開年度股東常會'),
    ('2020-06-15', '舉辦第一季法說會，說明營運與財務狀況'),
    ('2020-08-01', '設立 2-奈米研發實驗室於新竹園區'),
    ('2020-08-24', '舉辦 TSMC 2020 Tech Symposium 與 OIP 生態論壇（線上）'),
    ('2020-09-23', '預計為 Apple 生產 5 奈米 A14 處理器'),
    ('2020-12-10', '美國政府宣布限制華為獲取先進製程晶片'),
    ('2020-12-15', '公布第三季財報，顯示營收與獲利表現'),

    # 2021
    ('2021-03-12', '公布第一季財報'),
    ('2021-06-01', '舉辦線上 TSMC 技術研討會，介紹先進製程技術'),
    ('2021-06-09', '召開股東常會'),
    ('2021-06-15', '舉辦第二季法說會，說明營運與財務狀況'),
    ('2021-08-20', '舉辦 TSMC 2021 Tech Symposium 與 OIP 生態論壇'),
    ('2021-10-01', '宣布在美國亞利桑那州擴建半導體製造設施'),
    ('2021-10-15', '發布第三季財報，顯示營收與獲利成長'),

    # 2022
    ('2022-03-12', '公布第一季財報'),
    ('2022-06-16', '在美國聖塔克拉舉辦 TSMC 技術研討會，展示先進製程與封裝技術'),
    ('2022-06-30', '宣布在德國德累斯頓建立先進半導體製造廠'),
    ('2022-06-15', '舉辦第二季法說會，說明營運與財務狀況'),
    ('2022-08-24', '舉辦 TSMC 2022 Tech Symposium 與 OIP 生態論壇'),
    ('2022-10-26', '在美國聖塔克拉舉辦 OIP 生態論壇，與合作夥伴分享設計與製程創新'),
    ('2022-11-08', '在荷蘭阿姆斯特丹舉辦 OIP 生態論壇，拓展歐洲市場'),
    ('2022-12-10', '公布第三季財報，顯示營收與獲利表現'),

    # 2023
    ('2023-03-12', '公布第一季財報'),
    ('2023-06-16', '在美國聖塔克拉舉辦 TSMC 技術研討會，介紹最新製程與封裝技術'),
    ('2023-06-15', '舉辦第二季法說會，說明營運與財務狀況'),
    ('2023-08-01', '舉辦線上技術講座，探討半導體未來發展趨勢'),
    ('2023-09-11', '在美國伊利諾伊州舉辦虛擬技術講座，與學術界交流合作'),
    ('2023-10-15', '發布第三季財報，顯示營收與獲利表現'),

    # 2024
    ('2024-03-12', '公布第一季財報'),
    ('2024-04-24', '在美國聖塔克拉舉辦北美技術研討會，展示先進製程與封裝技術'),
    ('2024-06-15', '舉辦第二季法說會，說明營運與財務狀況'),
    ('2024-08-01', '舉辦線上技術講座，介紹最新製程與封裝技術'),
    ('2024-10-13', '發布第三季財報，顯示營收與獲利表現'),
    ('2024-12-06', '在荷蘭阿姆斯特丹舉辦中國 OIP 生態論壇，拓展歐洲市場'),

    # 2025
    ('2025-03-03', '宣布將投資 1000 億美元於美國，擴大半導體製造能力'),
    ('2025-03-12', '公布第一季財報'),
    ('2025-05-27', '宣布在德國慕尼黑設立新的晶片設計中心，支援歐洲客戶'),
    ('2025-06-15', '舉辦第二季法說會，說明營運與財務狀況'),
    ('2025-08-05', '發現商業機密外洩，對公司形象造成影響'),
    ('2025-08-06', '川普宣布對進口半導體徵收約 100% 的關稅，對在美國設廠或承諾設廠的公司予以豁免'),
    ('2025-09-24', '在美國聖塔克拉舉辦北美 OIP 生態論壇，與合作夥伴分享設計與製程創新'),
    ('2025-10-15', '發布第三季財報，顯示營收與獲利表現')
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
            messages.append(f"提醒：{name} 將於 {event_date_str} 發生")
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
    
