import os
import pandas as pd
from simulation import DATA_DIR  # 確保 DATA_DIR 來自 simulation.py

class TradingHistory:
    def __init__(self, initial_balance=100000, record_file='trading_history.txt'):
        self.balance = initial_balance
        self.holdings = []  # 用列表記錄每次買入的價格
        self.record_file = record_file
        self.transaction_id = self._get_last_transaction_id()  # 交易 ID 應該是整數
        self.held_stocks = 0  # 持有的股票數
        

    def get_balance(self):
        """取得目前可用餘額"""
        return self.balance
    
    def get_held_stocks(self):  
        return self.held_stocks

    def buy_stock(self, price):
        if self.balance >= price:  # 檢查是否有足夠的餘額
            self.balance -= price
            self.held_stocks += 1  # 增加持股數
            self.holdings.append(price)  # ✅ 記錄購買價格
            #self._record_transaction(price, None, None)  # ✅ 記錄交易，但還沒有賣出價和信號
            return True
        return False

    def sell_stock(self, price):
        if self.held_stocks > 0:  # 確保有持股
            self.balance += price
            self.held_stocks -= 1  # 減少持股數
            buy_price = self.holdings.pop(0)  # ✅ 取出最早買入的價格 (FIFO)
            signal = 1 if price > buy_price else 0 if price == buy_price else -1
            self._record_transaction(buy_price, price, signal)  # ✅ 記錄賣出
            return True
        return False

    def close_position(self, price):
        """平倉（賣出所有持有的股票）"""
        if self.holdings:
            for buy_price in self.holdings:
                profit = price - buy_price
                signal = 1 if profit > 0 else 0 if profit == 0 else -1
                self.balance += price
                self._record_transaction(buy_price, price, signal)
            self.holdings = []  # 清空持倉
            return True
        return False

    def _record_transaction(self, buy_price, sell_price, signal):
        """紀錄交易歷史"""
        with open(self.record_file, 'a') as f:
            f.write(f"  {self.transaction_id}          {buy_price}        {sell_price}         {signal}\n")
        self.transaction_id += 1  # ✅ 交易 ID 正確遞增

    def _get_last_transaction_id(self):
        """讀取交易紀錄，取得最後一筆交易的 ID，確保交易編號連續"""
        if not os.path.exists(self.record_file):
            return 1  # 如果沒有交易紀錄，從 1 開始

        with open(self.record_file, 'r') as f:
            lines = f.readlines()

        if len(lines) <= 1:  # 只有標題行，沒有交易記錄
            return 1

        last_line = lines[-1].strip().split()
        try:
            return int(last_line[0]) + 1  # 取得最後一筆交易編號並 +1
        except ValueError:
            return 1  # 若格式錯誤，重新從 1 開始
