import os
import logging
import datetime


def get_domain_links(domain_name_path):
    """Load domain links from a file."""
    if not os.path.exists(domain_name_path):
        raise FileNotFoundError(f"Domain file {domain_name_path} not found.")
    with open(domain_name_path, 'r', encoding='utf-8') as file:
        domains = file.readlines()
    domains_links = [f"{domain.strip()}" for domain in domains if domain.strip()]
    if not domains_links:
        logging.warning(f"No valid domains found in {domain_name_path}")
    return domains_links


async def save_articles_to_db(pool, articles):
    if not articles:
        print("⚠️ Không có bài viết nào để lưu.")
        return

    insert_query = """
        INSERT INTO articles (url, title, author, published_at, content)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (url) DO NOTHING;
    """

    async with pool.acquire() as conn:
        for article in articles:
            try:
                await conn.execute(
                    insert_query,
                    article.get("href"),
                    article.get("title"),
                    article.get("author"),
                    article.get("time"),
                    article.get("content"),
                )
                print(f"✅ Inserted: {article['title']}")
            except Exception as e:
                print(f"❌ Error inserting article {article.get('href')}: {e}")
                
                
import os
import asyncpg
from dotenv import load_dotenv

        
async def check_article_existed_in_db(url):
    load_dotenv()
    DATABASE_URL = os.getenv('DATABASE_URL')

    pool = await asyncpg.create_pool(DATABASE_URL)
    async with pool.acquire() as conn:
        query = "SELECT EXISTS(SELECT 1 FROM links WHERE url = $1)"
        result = await conn.fetchval(query, url)
        return result