# Stock


 ```
Stock/
│
├── app.py           # 主 Flask 應用程式文件
├── db.py            # 資料庫連線帳密
├── trade.py         # 負責交易的相關邏輯
├── templates/
│   ├── account.html     # 用戶當前個人資料(帳戶餘額/持有股票)  
│   ├── login.html       # 登入介面
│   ├── register.html    # 註冊介面
│   ├── transaction.html # 歷史交易紀錄顯示介面   
│   └── trade.html       # 交易介面(選擇股票/顯示該股票相關資訊)
└── static/
    ├── styles.css         
```


## ER-Diagram

<img width="761" alt="image" src="https://github.com/user-attachments/assets/e28f491d-0c30-4ca6-ad30-019debcacd5b">



## MySQL

```
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

```





