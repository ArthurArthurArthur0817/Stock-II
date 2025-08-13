import os
import pandas as pd
from simulation import DATA_DIR  # 確保 DATA_DIR 來自 simulation.py

def _to_float(x, default=0.0):
    try:
        return float(x)
    except (TypeError, ValueError):
        return default

def _to_int(x, default=0):
    try:
        return int(float(x))
    except (TypeError, ValueError):
        return default

class TradingHistory:
    def __init__(self, initial_balance=100000, record_file='trading_history.txt'):
        self.balance = _to_float(initial_balance)
        self.holdings = []
        self.record_file = record_file
        self.transaction_id = self._get_last_transaction_id()
        self.held_stocks = 0

    def get_balance(self):
        return _to_float(self.balance)
    
    def get_held_stocks(self):
        return _to_int(self.held_stocks)

    def buy_stock(self, price):
        price = _to_float(price)
        self.balance = _to_float(self.balance)
        self.held_stocks = _to_int(self.held_stocks)
        if self.balance >= price:
            self.balance -= price
            self.held_stocks += 1
            self.holdings.append(price)
            return True
        return False

    def sell_stock(self, price):
        price = _to_float(price)
        self.balance = _to_float(self.balance)
        self.held_stocks = _to_int(self.held_stocks)
        if self.held_stocks > 0:
            buy_price = _to_float(self.holdings.pop(0))
            self.balance += price
            self.held_stocks -= 1
            signal = 1 if price > buy_price else 0 if price == buy_price else -1
            self._record_transaction(buy_price, price, signal)
            return True
        return False

    def close_position(self, price):
        price = _to_float(price)
        self.balance = _to_float(self.balance)
        if self.holdings:
            total_stocks = len(self.holdings)
            for buy_price in self.holdings:
                buy_price = _to_float(buy_price)
                profit = price - buy_price
                signal = 1 if profit > 0 else 0 if profit == 0 else -1
                self._record_transaction(buy_price, price, signal)
            self.balance += price * total_stocks
            self.holdings = []
            self.held_stocks = 0
            return True
        return False

    def _record_transaction(self, buy_price, sell_price, signal):
        with open(self.record_file, 'a') as f:
            f.write(f"  {self.transaction_id}          {buy_price}        {sell_price}         {signal}\n")
        self.transaction_id += 1

    def _get_last_transaction_id(self):
        if not os.path.exists(self.record_file):
            return 1
        with open(self.record_file, 'r') as f:
            lines = f.readlines()
        if len(lines) <= 1:
            return 1
        last_line = lines[-1].strip().split()
        try:
            return int(last_line[0]) + 1
        except ValueError:
            return 1
