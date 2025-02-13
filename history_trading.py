import os

TRANSACTION_FILE = "transactions.txt"

def load_transactions():
    """讀取交易紀錄"""
    if not os.path.exists(TRANSACTION_FILE):
        return []
    
    transactions = []
    with open(TRANSACTION_FILE, "r") as file:
        for line in file.readlines()[1:]:  # 跳過標題
            parts = line.strip().split()
            transactions.append({
                "id": int(parts[0]),
                "stock_code": parts[1],
                "buy_price": float(parts[2]),
                "buy_qty": int(parts[3]),
                "sell_price": float(parts[4]),
                "sell_qty": int(parts[5]),
                "signal": int(parts[6])
            })
    return transactions

def get_transaction_history(last_n=10):
    """取得最近 N 筆交易紀錄"""
    transactions = load_transactions()
    return transactions[-last_n:]  # 取最近 N 筆

def calculate_profit_loss():
    """計算總盈虧"""
    transactions = load_transactions()
    profit = 0
    for t in transactions:
        if t["signal"] == -1 or t["signal"] == 0:  # 賣出或平倉
            profit += (t["sell_price"] - t["buy_price"]) * t["sell_qty"]
    return profit

def get_current_holdings():
    """取得目前持股數"""
    holdings = {}
    transactions = load_transactions()

    for t in transactions:
        stock = t["stock_code"]
        if stock not in holdings:
            holdings[stock] = 0
        holdings[stock] += t["buy_qty"] - t["sell_qty"]
    
    return {k: v for k, v in holdings.items() if v > 0}  # 只回傳有持股的股票
