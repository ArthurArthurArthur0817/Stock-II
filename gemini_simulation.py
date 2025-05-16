import google.generativeai as genai
import os

# 配置 Gemini API 密鑰
api_key = 'AIzaSyDQ3rFXvaefqgNuJ6tsL-L0JDDqjQDVq4Q'  # ← 請替換為你的 API 金鑰
genai.configure(api_key=api_key)

def analyze_trading_history():
    if not os.path.exists("trading_history.txt"):
        return "❌ 找不到交易紀錄！"

    try:
        with open("trading_history.txt", "r", encoding="utf-8") as f:
            trading_data = f.read().strip()

        if not trading_data:
            return "❌ 交易紀錄為空！"

        # 定義 AI 分析提示詞
        prompt = f"""
        讀取以下的股票交易紀錄：
        {trading_data}

        其中：
        - buy_price = 買入價格
        - sell_price = 賣出價格
        - signal = 1 (賺錢), -1 (虧損), 0 (打平)
        數據可能不多，但還是根據整體交易勝率(賺的次數/交易總次數)
        以及每次的進出的價格，給點簡單的建議，不要直接說無法判斷
        """

        # 呼叫 Gemini API
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(prompt)
        response.resolve()

        # 確保 Gemini API 有返回內容
        analysis_result = response.text.strip() if hasattr(response, "text") else "❌ AI 無法提供分析"

        # 寫入分析結果
        with open("simulation_analysis.txt", "w", encoding="utf-8") as f:
            f.write(analysis_result)

        return analysis_result

    except Exception as e:
        return f"❌ AI 分析時發生錯誤：{e}"

if __name__ == "__main__":
    result = analyze_trading_history()
    print(result)
