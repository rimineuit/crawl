import sys
import os
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
# Thêm thư mục gốc project vào sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
import sys
import json
import asyncio
import asyncpg
import os
from datetime import datetime
from dotenv import load_dotenv

from scrape.scrape_script.fireant import scrape_fireant_article
from utils import save_articles_to_db

load_dotenv()

async def main(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        raw_articles = json.load(f)

    enriched_articles = []

    for i, article in enumerate(raw_articles):
        url = article.get("href")
        if not url:
            print(f"⚠️ Bỏ qua bài {i} vì thiếu href.")
            continue

        print(f"🔍 [{i+1}/{len(raw_articles)}] Scraping: {url}")
        try:
            result = await scrape_fireant_article(url)
            if result:
                article.update(result)
                enriched_articles.append(article)
                print(f"✅ Scraped: {article['title']}")
            else:
                print(f"⚠️ Không lấy được dữ liệu từ {url}")
        except Exception as e:
            print(f"❌ Lỗi scrape {url}: {e}")

    # Lưu vào DB
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

    asyncio.run(main(sys.argv[1]))
