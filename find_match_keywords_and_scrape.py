
import os
import sys
# Thêm thư mục gốc của project vào sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
import asyncpg
import asyncio
from zoneinfo import ZoneInfo
from datetime import datetime
from crawl_and_scraper.scrape_articles.fireant_scrape_crawl4ai import scrape_fireant_article

def get_key_words(key_words_path='./crawl_and_scraper/key_words.txt'):
    """Load keywords from a file."""
    try:
        with open(key_words_path, 'r', encoding='utf-8') as file:
            key_words = file.readlines()
        return [word.strip() for word in key_words if word.strip()]
    except FileNotFoundError:
        logging.warning(f"Keywords file {key_words_path} not found. Returning empty list.")
        return []

def matching_links(links, keywords):
    """Filter links containing keywords in title or description."""
    result = []
    seen_urls = set()  # Lưu trữ các URL đã thấy để tránh trùng lặp
    for link in links:
        if any(
            keyword.lower() in link['title'].lower() or
            keyword.lower() in (link['description'] or '').lower()
            for keyword in keywords
        ):
            if link['href'] not in seen_urls:  # Kiểm tra trùng lặp dựa trên URL
                result.append(link)
                seen_urls.add(link['href'])
    return result

async def fetch_links_from_db(pool):
    """Fetch all links from the database."""
    vn_tz = ZoneInfo("Asia/Ho_Chi_Minh")
    async with pool.acquire() as conn:
        # Đặt múi giờ session
        await conn.execute("SET TIME ZONE 'Asia/Ho_Chi_Minh';")
        try:
            rows = await conn.fetch("""
                SELECT url, title, description, published_at, source
                FROM links
            """)
            # Chuyển đổi rows thành danh sách dictionary
            links = [
                {
                    'href': row['url'],
                    'title': row['title'],
                    'description': row['description'],
                    'source': row['source']
                }
                for row in rows
            ]
            logging.info(f"Fetched {len(links)} links from database")
            return links
        except Exception as e:
            logging.error(f"Error fetching links from database: {e}")
            return []

async def filter_links_by_keywords(db_url, key_words_path='./crawl_and_scraper/key_words.txt'):
    """Fetch links from database and filter by keywords."""
    if not db_url:
        raise ValueError("DATABASE_URL is not set")

    # Load keywords
    keywords = get_key_words(key_words_path)
    if not keywords:
        logging.warning("No keywords loaded. Returning empty list.")
        return []

    # Kết nối cơ sở dữ liệu
    pool = await asyncpg.create_pool(db_url)
    try:
        # Lấy links từ cơ sở dữ liệu
        links = await fetch_links_from_db(pool)
        if not links:
            logging.warning("No links found in database.")
            return []

        # Lọc links theo keywords
        matched_links = matching_links(links, keywords)
        logging.info(f"Found {len(matched_links)} links matching keywords")

        return matched_links
    except Exception as e:
        logging.error(f"Error in filter_links_by_keywords: {e}")
        return []
    finally:
        await pool.close()
        
# from dotenv import load_dotenv 
# load_dotenv()

# if __name__ == "__main__":

#     async def main():

#         DATABASE_URL = os.getenv('DATABASE_URL')

#         # Chạy hàm lọc links
        
#         matched_links = await filter_links_by_keywords(DATABASE_URL)
#         # Crawl lại từng link trong matched_links
#         articles = []
#         for link in matched_links:
#             url = link['href']
#             logging.info(f"Re-scraping article: {url}")
#             article = await scrape_fireant_article(url)
#             if article:
#                 articles.append(article)
#             else:
#                 logging.error(f"Failed to re-scrape article: {url}")
#         return articles
        
#     articles = asyncio.run(main())
#     for a in articles:
#         print(a)