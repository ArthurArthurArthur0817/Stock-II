# 結合策略模擬與生成式 AI 的互動式投資教育系統
## 發展動機與目標
目前市面上缺乏針對零基礎使用者設計的模擬投資平台，導致許多初學者必須經歷多次嘗試與失敗，才能逐步累積投資經驗。  
因此，本專題旨在打造一個結合 **Python Flask** 與 **Gemini AI** 的智慧投資學習平台，協助新手投資者在無基礎的情況下也能有效入門投資，讓投資變得更簡單且可學習。

---

## 產品特色 / 發展現況說明

- **智能股票推薦與報酬率模擬**
  - 使用者只需根據自身需求填寫設計好的表單，系統即可推薦合適股票。
  - 提供報酬率模擬計算功能。

- **模擬交易系統**
  - 使用者可進行股票的模擬買賣操作。
  - 搭配 **超過15種交易策略函數**，輸入股票並選擇指定交易策略，即可獲得該股票套用策略的分析結果。
  - 若有不理解之處，可將分析結果提交給 AI，系統會：
    - 解釋策略數值意義與股票分析結果。
    - 反問使用者相關問題，確認學習狀況，實現 **互動式學習**。

- **歷史數據模擬交易**
  - 系統會隨機挑選一支股票的歷史股市資料，使用者無法得知實際股票代號。
  - 使用者只能透過圖表與自身判斷進行買賣操作。
  - 模擬結束後，AI 會：
    - 分析使用者操作結果。
    - 提供策略建議，幫助使用者從模擬中反思與成長。



 ```
Stock/
│
├── app.py           # 主 Flask 應用程式文件
├── db.py            # 資料庫連線帳密
├── trade.py         # 負責交易的相關邏輯
├── simulation.py
├── gemini.py
├── gemini_learn.py
├── gemini_simulation.py
├── history_trading.py
├── news.py
├── risk_analysis.py
├── templates/
│   ├── account.html     # 用戶當前個人資料(帳戶餘額/持有股票)  
│   ├── login.html       # 登入介面
│   ├── register.html    # 註冊介面
│   ├── transaction.html # 歷史交易紀錄顯示介面   
│   └── trade.html       # 交易介面(選擇股票/顯示該股票相關資訊)
│   ├── K_chart.html
│   ├── analysis_tools.html
│   ├── basic.html
│   ├── dictionary.html
│   ├── journal.html
│   ├── main.html
│   ├── market.html
│   ├── news.html
│   ├── risk.html
│   ├── risk_result.html
│   ├── roi.html
│   ├── simulation.html
│   ├── teach.html
│   └── trans_related.html      
└── static/
    ├── styles.css         


## ER-Diagram

<img width="761" alt="image" src="https://github.com/user-attachments/assets/e28f491d-0c30-4ca6-ad30-019debcacd5b">



## MySQL


use my_database;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
	balance DECIMAL(10, 2) DEFAULT 2000000.00, 
    password VARCHAR(255) NOT NULL
);

CREATE TABLE portfolios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    balance DECIMAL(10, 2) DEFAULT 2000000.00,  
    stock VARCHAR(255),
    quantity INT DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    stock VARCHAR(255),
    quantity INT,
    price DECIMAL(10, 2),
    transaction_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    type ENUM('BUY', 'SELL') NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);



UPDATE portfolios p1
JOIN (
    SELECT user_id, stock, SUM(quantity) AS total_quantity
    FROM portfolios
    GROUP BY user_id, stock
) p2 ON p1.user_id = p2.user_id AND p1.stock = p2.stock
SET p1.quantity = p2.total_quantity;



DELETE p1
FROM portfolios p1
JOIN portfolios p2
ON p1.user_id = p2.user_id AND p1.stock = p2.stock
WHERE p1.id > p2.id;



SET SQL_SAFE_UPDATES=0;



CREATE TABLE ai_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50),                      -- 使用者 ID
    stock_code VARCHAR(10),                   -- 股票代號（如 2330）
    simulation_start_date DATE,               -- 模擬開始日期（從歷史資料擷取）
    content TEXT,                             -- AI 分析文字結果
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP  -- 紀錄建立時間
);




ALTER TABLE ai_logs
ADD COLUMN win_rate FLOAT DEFAULT 0,
ADD COLUMN profit FLOAT DEFAULT 0;


CREATE TABLE trading_history_rank AS
SELECT 
    u.username,
    ROUND(AVG(a.win_rate), 4) AS avg_win_rate,
    ROUND(SUM(a.profit), 2) AS total_profit
FROM 
    users u
JOIN 
    ai_logs a ON u.id = a.user_id
GROUP BY 
    u.username;

for使用教學:
ALTER TABLE users ADD COLUMN home_tutorial_seen TINYINT(1) NOT NULL DEFAULT 0;


```





