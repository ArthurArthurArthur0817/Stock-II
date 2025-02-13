import yfinance as yf
from db import get_connection

def get_stock_info(stock_symbol):
    """
    獲取股票的基本資訊，僅處理台股代碼 (如 2330.TW)。
    :param stock_symbol: 股票代碼（必須包含 .TW 後綴）
    :return: (股票資訊字典, 錯誤訊息)
    """
    try:
        # 使用 yfinance 獲取股票資訊
        stock = yf.Ticker(stock_symbol)
        info = stock.info

        # 構建股票資訊字典
        stock_info = {
            "symbol": stock_symbol.split('.')[0],  # 提取股票代碼（去除 ".TW"）
            "name": info.get("longName"),         # 股票名稱
            "sector": info.get("sector"),         # 所屬行業
            "market_cap": info.get("marketCap"),  # 市值
            "current_price": info.get("currentPrice"),  # 目前股價
        }

        # 驗證是否缺少必要的欄位資訊
        missing_fields = [key for key, value in stock_info.items() if value is None]
        if missing_fields:
            return None, f"Some stock information is missing: {', '.join(missing_fields)}."

        return stock_info, None  # 回傳股票資訊與無錯誤訊息
    except Exception as e:
        # 若有錯誤，回傳錯誤訊息
        return None, f"Error fetching stock info: {e}"

def process_trade(user_id, stock, quantity, price, trade_type):
    """
    處理交易功能，包括買入與賣出股票。
    :param user_id: 使用者 ID
    :param stock: 股票代碼
    :param quantity: 交易數量
    :param price: 交易價格
    :param trade_type: 交易類型 ('BUY' 或 'SELL')
    :return: (是否成功, 錯誤或成功訊息)
    """
    try:
        # 建立資料庫連線與游標
        connection = get_connection()
        cursor = connection.cursor()

        if trade_type == 'BUY':  # 買入交易
            total_cost = quantity * price  # 總花費計算
            cursor.execute("SELECT balance FROM users WHERE id = %s", (user_id,))
            balance_result = cursor.fetchall()
            balance = balance_result[0][0] if balance_result else None

            if balance is None:  # 檢查使用者是否存在
                return False, "User not found."

            if balance < total_cost:  # 檢查餘額是否足夠
                return False, "Insufficient balance to complete the transaction."

            # 扣除使用者餘額
            cursor.execute("UPDATE users SET balance = balance - %s WHERE id = %s", (total_cost, user_id))
            # 更新或新增持股數量
            cursor.execute(
                "INSERT INTO portfolios (user_id, stock, quantity) VALUES (%s, %s, %s) "
                "ON DUPLICATE KEY UPDATE quantity = quantity + %s",
                (user_id, stock, quantity, quantity)
            )

        elif trade_type == 'SELL':  # 賣出交易
            # 查詢使用者是否擁有該股票
            cursor.execute("SELECT quantity FROM portfolios WHERE user_id = %s AND stock = %s", (user_id, stock))
            quantity_result = cursor.fetchall()
            
            # 取得現有持股數量，若無記錄則設為 0
            current_quantity = quantity_result[0][0] if quantity_result else 0

            # 檢查是否有足夠持股
            if current_quantity <= 0 or current_quantity < quantity:  
                return False, "Insufficient stock quantity to complete the transaction."

            # 計算總收入
            total_earnings = quantity * price

            # 更新使用者餘額
            cursor.execute("UPDATE users SET balance = balance + %s WHERE id = %s", (total_earnings, user_id))

            # 計算剩餘數量
            new_quantity = current_quantity - quantity
            if new_quantity == 0:  # 如果全部賣出，刪除記錄
                cursor.execute("DELETE FROM portfolios WHERE user_id = %s AND stock = %s", (user_id, stock))
            else:  # 否則更新剩餘數量
                cursor.execute(
                    "UPDATE portfolios SET quantity = %s WHERE user_id = %s AND stock = %s",
                    (new_quantity, user_id, stock)
                )
        else:
            return False, "Invalid trade type. Must be 'BUY' or 'SELL'."  # 檢查交易類型是否有效


        # 記錄交易到交易表
        cursor.execute(
            "INSERT INTO transactions (user_id, stock, quantity, price, type) VALUES (%s, %s, %s, %s, %s)",
            (user_id, stock, quantity, price, trade_type)
        )
        connection.commit()  # 提交交易
        return True, "Transaction completed successfully."

    except Exception as e:
        # 捕捉例外並回傳錯誤訊息
        print(f"Error in process_trade for user {user_id}, stock {stock}: {e}")
        return False, f"Error processing trade: {e}"

    finally:
        # 確保游標與連線被正確關閉
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()
