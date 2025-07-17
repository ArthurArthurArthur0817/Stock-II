import google.generativeai as genai
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 配置 Gemini API 密鑰
api_key = ''  # ←🔹請替換為你的 API 金鑰
genai.configure(api_key=api_key)

def analyze_question():
    if not os.path.exists("question.txt"):
        return "❌ 找不到 question.txt，請先提交問題！"

    try:
        with open("question.txt", "r", encoding="utf-8") as f:
            questions = f.read().strip()

        if not questions:
            return "❌ question.txt 內容為空，請先輸入問題！"

        # 🔹 定義 Gemini 提示詞 (Prompt)
        prompt = f"""
        讀取question.txt內容中的問題，在"總而言之"，上面的回答是ai的回答，下面是使用者的回答，
        比對使用者跟ai的相似度，說出使用者的回答還有什麼缺失。
        
        問題：{questions}
        """

        # 🔹 呼叫 Gemini API 生成回答
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content(prompt)
        response.resolve()

        # 🔹 確保 Gemini API 有返回內容
        if hasattr(response, "text") and response.text:
            analysis_result = response.text.strip()

            # 🔹 將結果寫入 learn.txt
            with open("learn.txt", "w", encoding="utf-8") as f:
                f.write(analysis_result)

            return analysis_result
        else:
            return "❌ Gemini API 沒有返回結果"

    except Exception as e:
        return f"❌ Gemini 產生內容時發生錯誤：{e}"

if __name__ == "__main__":
    result = analyze_question()
    print(result.encode('utf-8').decode('utf-8'))

