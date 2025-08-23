import google.generativeai as genai
import re

# 配置 Gemini API 金鑰
api_key = ''
genai.configure(api_key=api_key)

def get_gemini_response(question):
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    response = model.generate_content(question)
    response.resolve()

    # 格式化文字
    formatted_text = re.sub(r'\*+', '', response.text)
    formatted_text = formatted_text.replace('•', '・')
    return formatted_text

