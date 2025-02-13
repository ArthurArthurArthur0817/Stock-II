import time
from GoogleNews import GoogleNews
import datetime
import urllib.parse

def clean_link(link):
    """ 修正錯誤連結，刪除 Google 追蹤參數 """
    if "&ved=" in link:
        link = link.split("&ved=")[0]  # 刪除 `&ved=` 之後的內容
    if "&usg=" in link:
        link = link.split("&usg=")[0]  # 刪除 `&usg=` 之後的內容
    link = urllib.parse.unquote(link).strip()  # 解碼 URL，移除空格
    return link

def fetch_news():
    """ 爬取最近 7 天的台積電新聞（最多 35 則） """
    query = "台積電"
    googlenews = GoogleNews(lang="zh-TW", region="TW")

    # 計算最近 7 天的日期範圍
    today = datetime.datetime.today()
    seven_days_ago = today - datetime.timedelta(days=7)
    from_date = seven_days_ago.strftime("%m/%d/%Y")
    to_date = today.strftime("%m/%d/%Y")

    # 設定新聞時間範圍並搜尋
    googlenews.clear()
    googlenews.set_time_range(from_date, to_date)

    # 取得新聞
    news_results = []
    seen_titles = set()  # 🔹 記錄已經出現的新聞標題，避免重複
    seen_links = set()  # 🔹 記錄已經出現的新聞連結，避免重複
    page = 1

    while len(news_results) < 35:
        try:
            googlenews.search(query)
            news = googlenews.result()

            print(f"📌 爬取第 {page} 頁新聞，獲取到 {len(news)} 則")  # Debug 訊息
            
            if not news:
                break

            for article in news:
                title = article.get('title', '')
                link = article.get('link', '')

                # 🔹 修正連結格式
                link = clean_link(link)

                # 🔹 避免重複標題或連結
                if title in seen_titles or link in seen_links:
                    continue

                # 🔹 避免無效連結（Yahoo 隱私頁面）
                if not link.startswith("http") or "consent.yahoo.com" in link:
                    continue

                seen_titles.add(title)  # 記錄標題，避免重複
                seen_links.add(link)  # 記錄連結，避免重複
                news_results.append({
                    'title': title,
                    'media': article.get('media', ''),
                    'date': article.get('date', ''),
                    'link': link  # 🔹 確保連結格式正確
                })

                # 🔹 如果超過 35 則，跳出迴圈
                if len(news_results) >= 35:
                    break

            googlenews.get_page(page)
            page += 1
            time.sleep(3)  # 🔹 避免過快請求被封鎖

        except urllib.error.HTTPError as e:
            if e.code == 429:
                print("⚠️ Too Many Requests - 等待 10 秒後重試...")
                time.sleep(10)  # 如果被封鎖，等 10 秒後重試
                continue
            else:
                print(f"❌ 發生錯誤: {e}")
                break

    print(f"✅ 最終獲取到 {len(news_results)} 則新聞")  # Debug 確認
    return news_results if news_results else []  # 確保永遠回傳列表
