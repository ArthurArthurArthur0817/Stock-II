import google.generativeai as genai
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')


# 配置 API 密鑰
api_key = 'AIzaSyBE_AGHv3ncVmHrI0UI6M6tVGyFQ3CZrtY'
genai.configure(api_key=api_key)

def chatting(strategy_name, data):
    """
    使用 Gemini 模型分析策略數據，並將完整回應寫入 answer.txt
    """
    prompt = f"""
    請根據以下數據分析交易策略 '{strategy_name}' 的表現：
    
    {data}
    
    評估策略的淨利潤、回撤、交易總數、勝率、獲利因子及平均盈虧，並提供具體的結論。

    **回答格式請遵循以下規則：**
    分析結果:
    
    問題:
    問題1:
    
    參考回答:
    回答1:
    """

    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(prompt)
        response.resolve()
        full_text = response.text

        # 🔹 儲存完整回答到 answer.txt
        with open("answer.txt", "w", encoding="utf-8") as ans_file:
            ans_file.write(full_text)

        # 🔹 解析 answer.txt，將「參考回答」前的內容輸出到螢幕，剩餘內容寫入 question.txt
        process_answer_file("answer.txt")

        return full_text  # 回傳完整結果，仍然顯示在終端機
    except Exception as e:
        return f"Gemini 產生內容時發生錯誤：{e}"

def process_answer_file(file_path):
    """
    解析 answer.txt：
    1. 螢幕顯示「分析結果」內容（不包含「問題」和「參考回答」）
    2. 「問題」和「參考回答」寫入 question.txt
    """
    if not os.path.exists(file_path):
        print(f"❌ 找不到 answer.txt")
        return

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = file.read()

        # 🔍 先分割出「分析結果」與「問題」
        sections = data.split("問題:")

        if len(sections) > 1:
            analysis_result = sections[0].strip()  # 只包含「分析結果」
            questions_part = "問題:" + sections[1].strip()  # 從「問題」開始的部分

            # 🖥️ 只顯示「分析結果」
            print(analysis_result)

            # 再進一步拆分「問題」與「參考回答」
            question_sections = questions_part.split("參考回答:")

            if len(question_sections) > 1:
                questions_only = question_sections[0].strip()  # 只保留「問題」
                answers_only = question_sections[1].strip()  # 只保留「參考回答」

                # ✏️ 把「問題」與「參考回答」寫入 question.txt
                with open("question.txt", "w", encoding="utf-8") as q_file:
                    q_file.write(questions_only + "\n" + answers_only + "\n")
            else:
                print("❌ 無法找到 '參考回答:'，請檢查 Gemini 回應格式")
        else:
            print("❌ 無法找到 '問題:'，請檢查 Gemini 回應格式")
    except Exception as e:
        print(f"解析 answer.txt 時發生錯誤：{e}")


def parse_txt_file(file_path):
    """
    讀取並解析 analysis_results.txt
    """
    if not os.path.exists(file_path):
        print(f"❌ 找不到檔案：{file_path}")  # 🔴 確保 Flask 真的有找到檔案
        return "找不到分析結果檔案！請先執行策略分析。"

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = file.read()

        # 解析出策略名稱
        first_line = data.split("\n")[0]  # 讀取第一行策略名稱
        strategy_name = first_line.replace("---", "").strip()  # 移除 "---"

        print(f" 讀取策略：{strategy_name}")  #  確保程式有正確讀取策略名稱

        return chatting(strategy_name, data)
    except Exception as e:
        print(f" 讀取檔案時發生錯誤：{e}")
        return f"讀取檔案時發生錯誤：{e}"

if __name__ == "__main__":
    result = parse_txt_file("analysis_results.txt")
    print(result)
