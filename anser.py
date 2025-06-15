import os
import sys
# Thêm thư mục gốc của project vào sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
import asyncpg
import asyncio
from zoneinfo import ZoneInfo
from datetime import datetime
import json
# PyVi để tokenize và loại bỏ stop-words
from pyvi import ViTokenizer, ViPosTagger

# Jina AI reranker client
from jina import Client as JinaClient, Document

# # Gemini API (ví dụ giả sử có sdk như sau)
# from gemini_sdk import Gemini

#----------------------------------------
def load_vietnamese_stopwords(path='vietnamese_stopwords.txt'):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        return set()

def preprocess_query(query: str, stopwords_path='vietnamese_stopwords.txt') -> list[str]:
    stopwords = load_vietnamese_stopwords(stopwords_path)
    tokenized = ViTokenizer.tokenize(query)
    keywords = [word.replace('_', ' ')
                for word in tokenized.split()
                if word.replace('_', ' ') not in stopwords]
    return keywords

async def fetch_links_from_db(pool):
    """Fetch all links from the database."""
    async with pool.acquire() as conn:
        await conn.execute("SET TIME ZONE 'Asia/Ho_Chi_Minh';")
        rows = await conn.fetch("""
            SELECT link_id, url, title, description, published_at, source
            FROM links
        """)
        return [
            {
                'id': row['link_id'],
                'href': row['url'],
                'title': row['title'] or '',
                'description': row['description'] or '',
                'source': row['source']
            }
            for row in rows
        ]

def filter_by_keywords(links: list[dict], keywords: list[str]) -> list[dict]:
    """Lọc các link chứa bất kỳ từ khóa nào trong title/description."""
    result, seen = [], set()
    for link in links:
        text = (link['title'] + ' ' + link['description']).lower().replace('\n', '').strip()
        if any(kw.lower() in text for kw in keywords):
            if link['id'] not in seen:
                result.append(link)
                seen.add(link['id'])
    return result

import requests

async def rerank_with_jina(links: list[dict], query: str, jina_api_key: str):
    """
    Gửi documents và query đến Jina REST API để rerank.
    Trả về danh sách link['id'] đã được sắp xếp theo độ liên quan.
    """
    url = 'https://api.jina.ai/v1/rerank'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {jina_api_key}'
    }

    documents = [link['title'] + '\n' + link['description'] for link in links]
    data = {
        "model": "jina-reranker-v2-base-multilingual",
        "query": query,
        "top_n": str(len(documents)),  # rerank tất cả
        "documents": documents,
        "return_documents": False
    }

    response = requests.post(url, headers=headers, json=data)
    json_data = json.loads(response.content)

    # Lấy danh sách index đã reranked
    indices = [item["index"] for item in json_data["results"]]

    # Trả về danh sách link['id'] theo thứ tự reranked
    return [links[i]['id'] for i in indices]


async def process_user_query(db_url: str,
                             query: str,
                             jina_endpoint: str):
    """Toàn bộ flow từ query → preproc → fetch → filter → rerank"""
    if not all([db_url, query, jina_endpoint]):
        raise ValueError("Thiếu config (DATABASE_URL / JINA_ENDPOINT.")

    # 1. Preprocess
    keywords = preprocess_query(query)
    if not keywords:
        logging.warning("Query sau preproc không còn từ khóa.")
        return []
    # 2. Lấy tất cả links
    pool = await asyncpg.create_pool(db_url)
    try:
        links = await fetch_links_from_db(pool)
        if not links:
            return []

        # 3. Filter theo từ khóa
        filtered = filter_by_keywords(links, keywords)
        if not filtered:
            return []
        # 4. Rerank với Jina
        ranked = await rerank_with_jina(filtered, query, jina_endpoint)
        # 5. Chọn top 5 
        top_ids = ranked[:5]
        top_links = [link for link in filtered if link['id'] in top_ids]
        return top_links


    finally:
        await pool.close()

#----------------------------------------
# Ví dụ cách gọi trong main
if __name__ == "__main__":
    import dotenv
    dotenv.load_dotenv()

    db_url = os.getenv("DATABASE_URL")
    jina_ep = os.getenv("JINA_ENDPOINT")
    user_query = input("Nhập câu truy vấn của bạn: ")
    results = asyncio.run(process_user_query(db_url, user_query, jina_ep))
    print(results)