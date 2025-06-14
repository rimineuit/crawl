import sys
import os
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
# Thêm thư mục gốc project vào sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
import sys
import json
import asyncio
from datetime import datetime
import asyncpg
from dotenv import load_dotenv
import os

from scrape.scrape_script.cafef import scrape_cafef_requests
from utils import save_articles_to_db

load_dotenv()

async def main(json_path):
    # 1. Đọc JSON input
    with open(json_path, 'r', encoding='utf-8') as f:
        articles = json.load(f)

    enriched_articles = []
    for i, article in enumerate(articles):
        url = article.get("href")
        if not url:
            print(f"⚠️ Bỏ qua bài {i} vì thiếu href.")
            continue

        print(f"🔍 [{i+1}/{len(articles)}] Scraping: {url}")
        try:
            content_data = scrape_cafef_requests(url) 
            if isinstance(content_data, dict):
                article.update(content_data)
            else:
                article["content"] = content_data

            enriched_articles.append(article)
            print(f"✅ Scraped: {article['title']}")
        except Exception as e:
            print(f"❌ Lỗi scrape {url}: {e}")

    # 2. Lưu vào DB
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ Thiếu biến môi trường DATABASE_URL")
        return

    try:
        pool = await asyncpg.create_pool(dsn=db_url)
        await save_articles_to_db(pool, enriched_articles)
    finally:
        await pool.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Cần truyền đường dẫn file JSON.")
        sys.exit(1)

    json_path = sys.argv[1]
    asyncio.run(main(json_path))
