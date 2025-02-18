import pandas as pd
import yfinance as yf
import talib
from datetime import datetime, timedelta

def assess_risk(row):
    """根據技術指標評估股票風險"""
    if row['ADX'] > 25 or row['RSI'] > 70 or row['RSI'] < 30 or abs(row['MACD_Hist']) > 0.5:
        return "高風險"
    elif row['ADX'] < 20 and 40 <= row['RSI'] <= 60 and abs(row['MACD_Hist']) < 0.3:
        return "低風險"
    else:
        return "中等風險"

def analyze_stock_risk(stock_code):
    """下載股票數據，計算技術指標並評估風險，回傳最新的風險等級"""
    try:
        print(f"📊 正在分析 {stock_code} ...")

        # 設定時間範圍（最近 6 個月）
        today = datetime.today().strftime("%Y-%m-%d")
        start_date = (datetime.today() - timedelta(days=180)).strftime("%Y-%m-%d")

        print(f"📅 下載數據範圍：{start_date} ~ {today}")
        df = yf.download(stock_code, start=start_date, end=today)

        if df.empty:
            print(f"⚠ {stock_code} 無法下載數據，可能是無效代碼。")
            return stock_code, "無數據"

        # 確保欄位是平坦名稱
        df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]

        # 清理數據
        df = df.dropna()

        # 計算技術指標
        df['ADX'] = talib.ADX(df['High'].to_numpy(), df['Low'].to_numpy(), df['Close'].to_numpy(), timeperiod=14)
        df['RSI'] = talib.RSI(df['Close'].to_numpy(), timeperiod=14)
        df['MACD'], df['MACD_Signal'], df['MACD_Hist'] = talib.MACD(df['Close'].to_numpy(), fastperiod=12, slowperiod=26, signalperiod=9)

        # 計算風險等級
        df['風險評估'] = df.apply(assess_risk, axis=1)

        # 取得最新日期的風險評估結果
        latest_data = df.dropna().iloc[-1] if not df.dropna().empty else None

        if latest_data is not None:
            latest_risk = latest_data["風險評估"]
            print(f"✅ {stock_code} 目前風險等級：{latest_risk}")
            return stock_code, latest_risk
        else:
            print(f"⚠ {stock_code} 數據不足，無法評估風險。")
            return stock_code, "數據不足"

    except Exception as e:
        print(f"❌ {stock_code} 處理時發生錯誤: {e}")
        return stock_code, "錯誤"

def filter_stocks_by_type(stock_type, csv_path="filtered_top2.csv"):
    """篩選符合 stock_type 的股票，並回傳風險分析結果"""
    try:
        df = pd.read_csv(csv_path, dtype=str)  # 確保數據以字串處理
        if df.shape[1] < 3:
            print("⚠ CSV 檔案格式錯誤。")
            return []

        # 篩選符合 stock_type 的股票
        filtered_df = df[df.iloc[:, 2] == str(stock_type)]
        stock_codes = filtered_df.iloc[:, 0].tolist()

        if stock_codes:
            print(f"✅ 符合類型 {stock_type} 的股票代碼：{stock_codes}")
            stock_risk_results = [analyze_stock_risk(stock) for stock in stock_codes]
            return stock_risk_results
        else:
            print(f"⚠ 沒有符合類型 {stock_type} 的股票。")
            return []

    except Exception as e:
        print(f"❌ 讀取 CSV 檔案時發生錯誤: {e}")
        return []

def process_stock_type(stock_type):
    """處理股票類型並回傳分析結果"""
    print(f"🔎 收到的 stock_type: {stock_type}")
    return filter_stocks_by_type(stock_type)
