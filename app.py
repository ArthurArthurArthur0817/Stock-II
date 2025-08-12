from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from db import get_connection
from trade import get_stock_info, process_trade
from news import fetch_news
import datetime
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
import time
import base64
from strategies import rsi,momentum  
import subprocess
import os
import importlib
from simulation import fetch_stock_data,plot_stock_data,get_random_stock
from history_trading import TradingHistory
from risk_analysis import  process_stock_type
import math
from industry_simulation import trading_industry

app = Flask(__name__)
app.secret_key = 'your_secret_key'

trading_history = TradingHistory()
from simulation import DATA_DIR  # 匯入 DATA_DIR





@app.route('/')
def main():
    return render_template('main.html')
     
# 登入頁面
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            connection = get_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
            user = cursor.fetchone()
            if user:
                session['user_id'] = user['id']
                return redirect(url_for('main'))
            else:
                flash("Invalid username or password.")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'connection' in locals():
                connection.close()
    return render_template('login.html')


# 註冊頁面
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
            connection.commit()
            #flash("Registration successful. Please log in.")
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"Error: {e}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'connection' in locals():
                connection.close()
    return render_template('register.html')



@app.route('/check_login')
def check_login():
    if 'user_id' in session:
        return jsonify({"logged_in": True})
    return jsonify({"logged_in": False})
@app.route('/logout')
def logout():
    session.pop('user_id', None)  # 清除 session
    return redirect(url_for('login'))  # 重新導向到登入頁面



# 計算風險分數的函式
def calculate_risk_score(answers):
    """計算使用者的投資風險評估分數"""
    score = sum(map(int, answers.values()))  # 將所有選項數值加總

    # 根據分數分類風險類型
    if score <= 10:
        return "保守型投資者", -1
    elif 11 <= score <= 18:
        return "穩健型投資者", 0
    else:
        return "積極型投資者", 1




# 用戶帳戶頁面
@app.route('/account')
def account():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        
        # 查詢用戶資產
        cursor.execute("SELECT balance FROM users WHERE id = %s", (session['user_id'],))
        user_balance = cursor.fetchone()
        
        if user_balance is None:
            flash('No portfolio found for this user. Please check your data.')
            return redirect(url_for('account'))

        user_balance = user_balance['balance']
        
        # 查詢用戶持有的股票並合併相同股票的數量
        cursor.execute("""
            SELECT stock, SUM(quantity) as total_quantity
            FROM portfolios
            WHERE user_id = %s
            GROUP BY stock
        """, (session['user_id'],))
        stocks = cursor.fetchall()
        
        # 獲取 portfolios 表中的數據
        cursor.execute("SELECT * FROM portfolios WHERE user_id = %s", (session['user_id'],))
        portfolios = cursor.fetchall()

        # 為每支股票添加即時價格
        for portfolio in portfolios:
            stock_symbol = portfolio['stock']
            stock_info, error = get_stock_info(stock_symbol)
            portfolio['price'] = stock_info['current_price'] if stock_info else None
            
            
        
            
    except Exception as e:
        flash(f"An error occurred: {str(e)}")
        return redirect(url_for('account'))
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()
    
    return render_template('account.html', balance=user_balance, stocks=stocks, portfolios=portfolios)




@app.route('/trade', methods=['GET', 'POST'])
def trade():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    stock_info = session.get("stock_info")  # 嘗試從 session 取回上次選擇的股票
    current_price = None
    strategy_result = None  # **新增變數來儲存策略結果**

    now = datetime.datetime.now()
    start_time = now.replace(hour=9, minute=0, second=0, microsecond=0)
    end_time = now.replace(hour=13, minute=30, second=0, microsecond=0)
    is_trading_time = start_time <= now <= end_time

    if request.method == 'POST':
        if 'get_stock_info' in request.form:
            stock_symbol = request.form['stock'].strip()
            if not stock_symbol.isdigit() or (len(stock_symbol) not in [4, 5, 6]):
                flash("Stock symbol must be a 4, 5, or 6-digit code representing a Taiwan stock.")
                return render_template('trade.html', stock_info=None, is_trading_time=is_trading_time, strategy_result=None)

            stock_symbol = f"{stock_symbol}.TW"
            stock_info, error_message = get_stock_info(stock_symbol)
            if error_message:
                flash(error_message)
                return render_template('trade.html', stock_info=None, is_trading_time=is_trading_time, strategy_result=None)

            session["stock_info"] = stock_info  # **將股票資訊存入 session**
        
        elif 'apply_strategy' in request.form:
            selected_strategy = request.form['strategy']
            investment_amount = request.form.get('investment_amount', 0)  # 取得投資金額
            strategy_module = f"strategies.{selected_strategy}"

            if stock_info and isinstance(stock_info, dict) and 'symbol' in stock_info:
                try:
                    strategy = importlib.import_module(strategy_module)
                    strategy_result = strategy.run(stock_info['symbol'] + ".TW", float(investment_amount))  # **傳入投資金額**
                except ModuleNotFoundError:
                    flash("Strategy module not found.")
                except AttributeError:
                    flash("Strategy module does not contain a 'run' function.")
            else:
                flash("Stock information is not available or incomplete.")

    return render_template('trade.html', stock_info=stock_info, is_trading_time=is_trading_time, strategy_result=strategy_result)



@app.route('/ai_analysis', methods=['POST'])
def ai_analysis():
    txt_path = "analysis_results.txt"

    # 檢查分析結果檔案是否存在
    if not os.path.exists(txt_path):
        return jsonify({"analysis_result": "❌ 找不到分析結果檔案！"})

    try:
        # 執行 Gemini 分析
        process = subprocess.run(["python", "gemini.py"], capture_output=True, text=True, encoding="utf-8")

        # 如果執行失敗，返回錯誤訊息
        if process.returncode != 0:
            error_msg = f"⚠️ 執行 gemini.py 失敗：{process.stderr.strip()}"
            print(error_msg)
            return jsonify({"analysis_result": error_msg})

        # 取得 Gemini 分析結果
        analysis_result = process.stdout.strip()  # 確保不會是 None 或空字串

        if not analysis_result:  # 確保 stdout 真的有內容
            return jsonify({"analysis_result": "⚠️ AI 沒有回傳分析結果"})

        # 只保留「分析結果」，去掉「問題」及後續內容
        filtered_result = analysis_result.split("參考回答:")[0].strip() if "參考回答:" in analysis_result else analysis_result

        print(f"✅ AI 分析結果：\n{filtered_result}")

        # 以 JSON 格式返回
        return jsonify({"analysis_result": filtered_result})

    except Exception as e:
        return jsonify({"analysis_result": f"⚠️ 發生錯誤：{str(e)}"})
    
    
@app.route("/save_question", methods=["POST"]) 
def save_question(): 
    data = request.get_json()
    question = data.get("question", "").strip() if data else ""
    print(f"收到請求數據: {request.data}")
    print(f"解析 JSON: {request.get_json()}")

    if not question:
        return jsonify({"message": "問題不能為空"}), 400

    try:
        with open("question.txt", "a", encoding="utf-8") as f:
            f.write(question + "\n")
        return jsonify({"message": "問題已成功儲存！"})
    except Exception as e:
        return jsonify({"message": f"寫入失敗: {str(e)}"}), 500



@app.route("/process_question", methods=["POST"])
def process_question():
    try:
        learn_path = "learn.txt"

        # 🔹 確保 subprocess 直接將輸出寫入 learn.txt
        with open(learn_path, "w", encoding="utf-8") as learn_file:
            result = subprocess.run(
                ["python", "gemini_learn.py"], 
                stdout=learn_file,   # 直接將 stdout 寫入檔案
                stderr=subprocess.PIPE,  # 保持 stderr 可讀取
                text=True
            )

        # 🔹 檢查 subprocess 是否成功執行
        if result.returncode != 0:
            return jsonify({"response": f"❌ Gemini 執行失敗：{result.stderr.strip()}"}), 500

        # 🔹 讀取 learn.txt 的內容
        if not os.path.exists(learn_path):
            return jsonify({"response": "❌ 找不到 learn.txt，請先執行 AI 分析！"}), 500

        try:
            with open(learn_path, "r", encoding="utf-8") as f:
                learn_content = f.read().strip()
        except UnicodeDecodeError:
            with open(learn_path, "r", encoding="latin-1") as f:
                learn_content = f.read().strip()

        print("📜 Learn.txt 內容：\n", learn_content)  # 🔹 顯示 learn.txt 內容到後端

        return jsonify({"response": learn_content})

    except Exception as e:
        return jsonify({"response": f"❌ 處理問題時發生錯誤：{str(e)}"}), 500

@app.route('/transaction')
def transaction():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    # 獲取 transaction 表中的數據
    cursor.execute("SELECT stock, quantity, price, transaction_time, type FROM transactions")
    transactions = cursor.fetchall()

    cursor.close()
    connection.close()
    return render_template('transaction.html', transactions=transactions)



@app.route('/teach')
def teach():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('teach.html')

@app.route('/risk')
def risk():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('risk.html')

@app.route('/result', methods=['POST'])
def result():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    answers = request.form
    stock_type = request.form.get('stock_type', "未選擇")
    
    # **取得股票風險分析結果**
    stock_risk_results = process_stock_type(stock_type)  

    # **計算用戶的風險評估類型**
    risk_type, risk_value = calculate_risk_score(answers)

    # **寫入風險數據到檔案**
    try:
        with open("risk_type.txt", "w", encoding="utf-8") as file:
            file.write(f"{stock_type},{risk_value}\n")
    except Exception as e:
        print(f"⚠️ 寫入 risk_type.txt 失敗: {e}")

    # **將風險數據傳給前端**
    return render_template("risk_result.html", 
                           risk_type=risk_type, 
                           stock_type=stock_type, 
                           stock_risk_results=stock_risk_results)





# 計算 CAGR
def calculate_cagr(stock_code):
    stock = yf.Ticker(stock_code)
    df = stock.history(period="max")  # 取得所有歷史數據

    if df.empty:
        return None  # 沒有數據則回傳 None

    start_price = df["Close"].iloc[0]  # 最早的收盤價
    end_price = df["Close"].iloc[-1]  # 最新的收盤價
    years = (df.index[-1] - df.index[0]).days / 365  # 計算經過的年數
    cagr = ((end_price / start_price) ** (1 / years)) - 1  # CAGR 計算公式
    return cagr * 100  # 轉成百分比

# 預測未來收益
def predict_future_value(initial_investment, cagr, months):
    years = months / 12  # 換算成年
    final_value = initial_investment * ((1 + cagr / 100) ** years)  # 預測最終價值
    profit = final_value - initial_investment  # 計算總收益
    return final_value, profit

# 將月份轉換為 yfinance 可接受的 period 格式
def get_valid_period(months):
    if months <= 1:
        return "1mo"
    elif months <= 3:
        return "3mo"
    elif months <= 6:
        return "6mo"
    elif months <= 12:
        return "1y"
    elif months <= 24:
        return "2y"
    elif months <= 60:
        return "5y"
    elif months <= 120:
        return "10y"
    else:
        return "max"

# 繪製 K 線圖
def plot_comparison(stock_code, months):
    period = get_valid_period(months)
    stock = yf.Ticker(stock_code)
    market = yf.Ticker("^TWII")  # 台灣加權指數

    df_stock = stock.history(period=period)
    df_market = market.history(period=period)

    print(df_stock.head())  # 檢查是否有資料
    print(df_market.head())  # 檢查是否有資料

    if df_stock.empty or df_market.empty:
        return None  # 沒數據就不畫圖

    df_stock["Return"] = df_stock["Close"].pct_change().cumsum() * 100
    df_market["Return"] = df_market["Close"].pct_change().cumsum() * 100

    plt.figure(figsize=(8, 5))
    plt.plot(df_stock.index, df_stock["Return"], label=f"{stock_code} (%)", color="blue")
    plt.plot(df_market.index, df_market["Return"], label="^TWII (%)", color="red")
    plt.xlabel("Period")
    plt.ylabel("Price change (%)")
    plt.title(f"{stock_code} vs ^TWII")
    plt.legend()
    plt.grid()

    img = io.BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()
    return f"data:image/png;base64,{plot_url}"



@app.route("/calculate", methods=["POST"])
def calculate():
    data = request.json
    stock_code = data.get("stock_code")
    initial_investment = float(data.get("initial_investment"))
    months = int(data.get("months"))

    cagr = calculate_cagr(stock_code)
    if cagr is None:
        return jsonify({"error": "股票代號無效或無數據"})

    final_value, profit = predict_future_value(initial_investment, cagr, months)
    plot_url = plot_comparison(stock_code, months)

    return jsonify({
        "cagr": round(cagr, 2),
        "final_value": round(final_value, 2),
        "profit": round(profit, 2),
        "plot_url": plot_url
    })


@app.route('/roi')
def roi():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('roi.html')


@app.route('/simulation')
def simulation():  
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # ✅ 每次都隨機選一支新的股票
    session['stock_code'] = get_random_stock()
    session['start_index'] = 0
    session['balance'] = 100_000
    clear_trading_history()

    # ✅ 嘗試抓股票資料（包含 retry 機制）
    max_retries = 3
    for i in range(max_retries):
        if fetch_stock_data(session['stock_code']):
            break
        else:
            print(f"第 {i+1} 次抓取失敗，稍後再試...")
            time.sleep(2 * (i + 1))  # 緩衝時間 2s, 4s, 6s
    else:
        return "無法獲取股票數據，請稍後再試"

    # ✅ 繪製股票圖
    plot_path = plot_stock_data(session['stock_code'], session['start_index'])
    if not plot_path:
        return "無法生成股票圖表，請稍後再試"
    
    # ✅ 最新股價
    latest_price_response = get_latest_price()
    latest_price = latest_price_response.json.get('latest_price', None)

    # ✅ 建立資料庫紀錄並寫入 stock_code 和模擬開始時間
    try:
        from db import get_connection
        conn = get_connection()
        cursor = conn.cursor()

        # 讀取最早的模擬起始日期
        df = pd.read_csv(os.path.join(DATA_DIR, f"{session['stock_code']}.csv"))
        simulation_start_date = df['Date'].iloc[0]

        insert_query = """
            INSERT INTO ai_logs (user_id, stock_code, simulation_start_date)
            VALUES (%s, %s, %s)
        """
        cursor.execute(insert_query, (session['user_id'], session['stock_code'], simulation_start_date))
        conn.commit()

        session['log_id'] = cursor.lastrowid
        cursor.close()
        conn.close()
        print(f"✅ 已寫入 log_id={session['log_id']}，模擬開始於 {simulation_start_date}")
    except Exception as e:
        print("❌ 建立資料庫紀錄失敗：", e)

    return render_template(
        'simulation.html',
        plot_path=plot_path,
        stock_code=session['stock_code'],
        latest_price=latest_price,
        balance=session['balance']
    )


@app.route('/get_latest_price')
def get_latest_price():
    stock_code = session.get('stock_code')
    if not stock_code:
        return jsonify({'error': '未選擇股票'})

    csv_path = os.path.join(DATA_DIR, f'{stock_code}.csv')
    if not os.path.exists(csv_path):
        return jsonify({'error': '股票數據不存在'})

    df = pd.read_csv(csv_path, parse_dates=['Date'])

    start_index = session.get('start_index', 0)
    end_index = start_index + 10
    if end_index > len(df):
        end_index = len(df)
    
    latest_price = df.iloc[end_index - 1]['Close']  # 取得目前區間的最新價格
    return jsonify({'latest_price': latest_price})


@app.route('/next_day')
def next_day():
    """顯示下一天的 K 線圖，並更新股價"""
    session['start_index'] += 1
    plot_path = plot_stock_data(session['stock_code'], session['start_index'])

    if not plot_path:
        return jsonify({'error': '已超出資料範圍'})

    # 取得最新股價，確保與 session['start_index'] 對應
    latest_price_response = get_latest_price()
    latest_price = latest_price_response.json['latest_price'] if 'latest_price' in latest_price_response.json else None

    return jsonify({'plot_path': plot_path, 'latest_price': latest_price})



held_stocks = 0  # 持有的股票數

@app.route("/get_stock_count", methods=["GET"])
def get_stock_count():
    return jsonify({"stock_count": 0})  # ✅ 無論如何，回傳 0


@app.route('/buy_stock', methods=['POST'])
def buy_stock():
    stock_code = session.get('stock_code')
    if not stock_code:
        return jsonify({'error': '未選擇股票'})

    latest_price_response = get_latest_price()
    latest_price = latest_price_response.json['latest_price'] if 'latest_price' in latest_price_response.json else None
    
    if latest_price is None:
        return jsonify({'error': '無法獲取最新股價'})

    if trading_history.buy_stock(latest_price):
        return jsonify({
            'success': True,
            'balance': trading_history.get_balance(),
            'stock_count': trading_history.get_held_stocks()  # ✅ 取得最新持股數
        })

    return jsonify({'error': '餘額不足'})


@app.route('/sell_stock', methods=['POST'])
def sell_stock():
    stock_code = session.get('stock_code')
    if not stock_code:
        return jsonify({'error': '未選擇股票'})

    latest_price_response = get_latest_price()
    latest_price = latest_price_response.json['latest_price'] if 'latest_price' in latest_price_response.json else None

    if latest_price is None:
        return jsonify({'error': '無法獲取最新股價'})

    if trading_history.sell_stock(latest_price):
        return jsonify({
            'success': True,
            'balance': trading_history.get_balance(),
            'stock_count': trading_history.get_held_stocks()  # ✅ 取得最新持股數
        })

    return jsonify({'error': '沒有可賣股票'})




@app.route('/close_position', methods=['POST'])
def close_position():
    """平倉：賣出所有持股"""
    stock_code = session.get('stock_code')
    if not stock_code:
        return jsonify({'error': '未選擇股票'})
    
    # 確保股價與 UI 顯示的一致
    latest_price_response = get_latest_price()
    latest_price = latest_price_response.json['latest_price'] if 'latest_price' in latest_price_response.json else None

    if latest_price is None:
        return jsonify({'error': '無法獲取最新股價'})

    if trading_history.close_position(latest_price):
        return jsonify({'success': True, 'balance': trading_history.get_balance()})
    
    return jsonify({'error': '沒有可平倉股票'})




@app.route('/get_balance')
def get_balance():
    """獲取帳戶餘額"""
    return jsonify({'balance': trading_history.get_balance()})


RECORD_FILE = "trading_history.txt"
def clear_trading_history():
    """清空交易紀錄 txt 檔案"""
    if os.path.exists(RECORD_FILE):
        with open(RECORD_FILE, 'w') as f:
            f.write("|---num---|-----buy_price-----|-------sell_price--------|----signal---|\n")  # 保留標題行


ANALYSIS_FILE = "simulation_analysis.txt"
@app.route("/run_ai_analysis", methods=["POST"])
def run_ai_analysis():
    # 先刪除舊的分析結果，確保每次都是最新的
    if os.path.exists(ANALYSIS_FILE):
        os.remove(ANALYSIS_FILE)
        
    #新增紀錄勝率 賺取金額區域
    trading_file = "trading_history.txt"
    initial_money = 100000.0
    current_money = initial_money
    win_count = 0
    total_count = 0

    if os.path.exists(trading_file):
        with open(trading_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for line in lines:
            if line.strip().startswith("|") or not line.strip():
                continue  # 跳過表頭或空行
            try:
                parts = line.strip().split()
                buy_price = float(parts[1])
                sell_price = float(parts[2])
                signal = int(parts[3])

                profit = sell_price - buy_price
                current_money += profit
                total_count += 1
                if signal == 1:
                    win_count += 1
            except Exception as e:
                print(f"❌ 解析交易紀錄失敗：{e}，跳過此行 -> {line}")

        win_rate = round(win_count / total_count, 4) if total_count > 0 else 0.0
        profit_total = round(current_money - initial_money, 2)

        # ✅ 更新 win_rate 和 profit 欄位進 ai_logs
        try:
            conn = get_connection()
            cursor = conn.cursor()

            update_profit_query = "UPDATE ai_logs SET win_rate = %s, profit = %s WHERE id = %s"
            cursor.execute(update_profit_query, (win_rate, profit_total, session.get('log_id')))
            conn.commit()

            cursor.close()
            conn.close()
            print(f"✅ 勝率與獲利已寫入資料庫 log_id={session.get('log_id')}")
        except Exception as e:
            print("❌ 更新 profit 和 win_rate 失敗：", e)
    else:
        print("❌ 找不到 trading_history.txt")

       
    subprocess.run(["python", "gemini_simulation.py"], check=True)
    
    analysis_result = "AI 分析失敗"
    if os.path.exists("simulation_analysis.txt"):
        with open("simulation_analysis.txt", "r", encoding="utf-8") as f:
            analysis_result = f.read().strip()

                # ✅ 將分析結果更新進既有紀錄
        try:
            conn = get_connection()
            cursor = conn.cursor()

            update_query = "UPDATE ai_logs SET content = %s WHERE id = %s"
            cursor.execute(update_query, (analysis_result, session.get('log_id')))
            conn.commit()

            cursor.close()
            conn.close()
            print(f"✅ 已將 AI 分析結果寫入資料庫 log_id={session.get('log_id')}")
        except Exception as e:
            print("❌ 更新資料庫失敗：", e)


    return jsonify({"success": True, "analysis_result": analysis_result})



@app.route('/journal')
def journal():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    try:
        user_id = session['user_id']

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # 撈用戶模擬紀錄
        query_logs = """
            SELECT user_id, stock_code, simulation_start_date, content, created_at
            FROM ai_logs
            WHERE user_id = %s
              AND content IS NOT NULL AND content <> ''
              AND created_at IS NOT NULL
            ORDER BY created_at DESC
        """
        cursor.execute(query_logs, (user_id,))
        logs = cursor.fetchall()

        # 撈用戶最近5筆非0的 win_rate
        query_win_rate = """
            SELECT win_rate, created_at
            FROM ai_logs
            WHERE user_id = %s
              AND win_rate IS NOT NULL
              AND win_rate != 0
            ORDER BY created_at DESC
            LIMIT 5
        """
        cursor.execute(query_win_rate, (user_id,))
        win_rate_rows = cursor.fetchall()

        # 反轉舊->新，並乘上 100 轉成百分比格式
        win_rate_data = []
        for row in reversed(win_rate_rows):
            win_rate_data.append({
                'win_rate': round(row['win_rate'] * 100, 2),
                'created_at': row['created_at'].strftime('%Y-%m-%d')
            })

        cursor.close()
        conn.close()

        return render_template("journal.html", logs=logs, win_rate_data=win_rate_data)

    except Exception as e:
        return f"讀取資料失敗：{e}"




@app.route("/trading_history_rank")
def trading_history_rank():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # 清空舊資料，重建排行榜
        cursor.execute("TRUNCATE TABLE trading_history_rank")

        # 更新排行榜資料
        cursor.execute("""
            INSERT INTO trading_history_rank (username, avg_win_rate, total_profit)
            SELECT 
                u.username,
                ROUND(AVG(a.win_rate), 4),
                ROUND(SUM(a.profit), 2)
            FROM 
                users u
            JOIN 
                ai_logs a ON u.id = a.user_id
            GROUP BY 
                u.username
        """)

        # 讀取排行榜資料（依勝率、獲利排序）
        cursor.execute("SELECT * FROM trading_history_rank ORDER BY avg_win_rate DESC, total_profit DESC")
        ranks = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template("trading_history_rank.html", ranks=ranks)
    except Exception as e:
        return f"❌ 發生錯誤：{e}"




@app.route('/dictionary')
def dictionary():
    return render_template('dictionary.html')  # 確保你有 dictionary.html 檔案

#相關新聞
@app.route('/news')
def news():
    """ 顯示特定股票的新聞頁面 """
    stock_name = request.args.get("stock_name")

    if not stock_name:
        return render_template('news.html', news_list=[], error="⚠️ 未提供股票名稱，請返回重新選擇！")

    print(f"📢 正在獲取 {stock_name} 的新聞...")
    news_list = fetch_news(stock_name)  # 🔹 傳入股票名稱來獲取對應新聞

    if not news_list:
        return render_template('news.html', news_list=[], error=f"⚠️ 目前沒有 {stock_name} 的新聞，請稍後再試！")

    return render_template('news.html', news_list=news_list, stock_name=stock_name)


#==============================================================================
#==============================================================================

from industry_simulation import (
    get_available_stocks,industry_plot_stock_data, indusrty_fetch_stock_data,
    compute_indicators, detect_upcoming_event, get_stock_dataframe,get_safe_start_index
)


@app.route('/industry_select_stock', methods=['GET', 'POST'])
def industry_select_stock():
    if request.method == 'POST':
        stock_code = request.form['stock']
        session['stock_code'] = stock_code
        
        # 修改：計算安全的開始索引，而不是從 0 開始
        df = get_stock_dataframe(stock_code)
        df = compute_indicators(df)
        session['start_index'] = get_safe_start_index(df)  # 從安全位置開始
        
        session['balance'] = 100_000
        return redirect(url_for('industry_simulation'))

    stocks = get_available_stocks()
    return render_template('industry_select_stock.html', stocks=stocks)

@app.route('/industry_simulation')
def industry_simulation():
    stock_code = session.get('stock_code')
    if not stock_code:
        return redirect(url_for('industry_select_stock'))

    csv_ready = fetch_stock_data(stock_code)
    if not csv_ready:
        return "無法獲取股票資料"

    #引用到錯誤的繪圖
    start_index = session.get('start_index', 0)
    plot_path = industry_plot_stock_data(stock_code, start_index+1)
    df = get_stock_dataframe(stock_code)
    indicators = compute_indicators(df)

    if start_index >= len(indicators):
        start_index = len(indicators) - 1

    latest_price = indicators.iloc[start_index]['Close']

    return render_template('industry_simulation.html', stock_code=stock_code,
                           plot_path=plot_path, latest_price=latest_price,
                           balance=session['balance'],
                           stock_count=trading_history.get_held_stocks())  # 加上這行

from flask import request, jsonify

@app.route('/industry_buy_stock', methods=['POST'])
def industry_buy_stock():
    stock_code = session.get('stock_code')
    if not stock_code:
        return jsonify({'error': '未選擇股票'}), 400

    current_price = request.json.get('current_price')
    if current_price is None:
        return jsonify({'error': '缺少價格'}), 400

    if trading_industry.buy(current_price):
        return jsonify({
            'success': True,
            'balance': trading_industry.get_balance(),
            'stock_count': trading_industry.get_held_stocks()
        })
    else:
        return jsonify({'error': '餘額不足'})

@app.route('/industry_sell_stock', methods=['POST'])
def industry_sell_stock():
    stock_code = session.get('stock_code')
    if not stock_code:
        return jsonify({'error': '未選擇股票'}), 400

    current_price = request.json.get('current_price')
    if current_price is None:
        return jsonify({'error': '缺少價格'}), 400

    if trading_industry.sell(current_price):
        return jsonify({
            'success': True,
            'balance': trading_industry.get_balance(),
            'stock_count': trading_industry.get_held_stocks()
        })
    else:
        return jsonify({'error': '沒有可賣股票'})

@app.route('/industry_close_position', methods=['POST'])
def industry_close_position():
    stock_code = session.get('stock_code')
    if not stock_code:
        return jsonify({'error': '未選擇股票'}), 400

    current_price = request.json.get('current_price')
    if current_price is None:
        return jsonify({'error': '缺少價格'}), 400

    if trading_industry.close_position(current_price):
        return jsonify({
            'success': True,
            'balance': trading_industry.get_balance(),
            'stock_count': trading_industry.get_held_stocks()
        })
    else:
        return jsonify({'error': '沒有可平倉股票'})


@app.route('/industry_get_balance')
def industry_get_balance():
    return jsonify({'balance': trading_industry.get_balance()})


@app.route("/industry_get_stock_count")
def industry_get_stock_count():
    return jsonify({"stock_count": trading_industry.get_held_stocks()})



@app.route('/industry_next_day')
def industry_next_day():
    session['start_index'] += 1
    stock_code = session.get('stock_code')
    df = get_stock_dataframe(stock_code)
    df = compute_indicators(df)
    idx = session['start_index']
        
    if idx >= len(df):
        return jsonify({'error': '已超出資料範圍'})
        
    plot_path = plot_stock_data(stock_code, idx)
        
    # 檢查圖片是否成功產生
    if plot_path is None:
        return jsonify({'error': '圖片產生失敗'})
        
    event_messages = detect_upcoming_event(stock_code, df, idx)
        
    # 安全處理 NaN 值的函數
    def safe_round(value, decimals=2):
        if pd.isna(value) or math.isnan(value) or math.isinf(value):
            return 0.0
        try:
            return round(float(value), decimals)
        except:
            return 0.0
        
    return jsonify({
        'plot_path': plot_path,
        'latest_price': safe_round(df.iloc[idx]['Close']),
        'rsi': safe_round(df.iloc[idx]['rsi']),
        'macd': safe_round(df.iloc[idx]['macd']),
        'adx': safe_round(df.iloc[idx]['adx']),
        'events': event_messages
    })

@app.route('/industry_get_stocks')
def industry_get_stocks():
    return jsonify({'stocks': get_available_stocks()})


if __name__ == '__main__':
    app.run(debug=True)
