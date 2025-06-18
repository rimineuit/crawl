import os
import sys
# Thêm thư mục gốc của project vào sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncpg
import asyncio
from zoneinfo import ZoneInfo
from datetime import datetime
import json
# PyVi để tokenize và loại bỏ stop-words
from scrape_articles_by_source import scrape_from_urls
# Jina AI reranker client
from jina import Client as JinaClient, Document

# # Gemini API (ví dụ giả sử có sdk như sau)
# from gemini_sdk import Gemini

#----------------------------------------

async def embedding_query_with_jina(query: str, api_key: str) -> list[float]:
    url = 'https://api.jina.ai/v1/embeddings'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    data = {
        "model": "jina-embeddings-v3",
        "task": "retrieval.query",
        "dimensions": 64,
        "input": [query]
    }

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()

    embedding = response.json()["data"][0]["embedding"]
    return embedding


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

async def fetch_top_links_by_embedding(pool, embedding: list[float], top_k: int = 10):
    async with pool.acquire() as conn:
        query = """
            SELECT link_id, url, title, description, published_at, source
            FROM links
            WHERE embedding IS NOT NULL
            ORDER BY embedding <#> $1
            LIMIT $2
        """
        rows = await conn.fetch(query, embedding, top_k)
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
        "top_n": "5",
        "documents": documents,
        "return_documents": False
    }

    response = requests.post(url, headers=headers, json=data)
    json_data = json.loads(response.content)

    # Lấy danh sách index đã reranked
    indices = [item["index"] for item in json_data["results"]]

    # Trả về danh sách link['id'] theo thứ tự reranked
    return [links[i]['id'] for i in indices]

def list_to_pgvector(v):
    return f'[{", ".join(f"{x:.8f}" for x in v)}]'

async def process_user_query(db_url: str,
                             query: str,
                             jina_api_key: str):
    if not all([db_url, query, jina_api_key]):
        raise ValueError("Thiếu config (DATABASE_URL / JINA_ENDPOINT.")

    pool = await asyncpg.create_pool(db_url)
    try:
        # 1. Embedding query
        query_vector = list_to_pgvector(await embedding_query_with_jina(query, jina_api_key))

        # 2. Lấy top links theo vector similarity
        top_links = await fetch_top_links_by_embedding(pool, query_vector, top_k=20)

        if not top_links:
            return []

        # 3. Rerank lại với Jina
        reranked_ids = await rerank_with_jina(top_links, query, jina_api_key)

        # 4. Trả về top 5 kết quả sau rerank
        top_ids = reranked_ids[:5]
        return [link for link in top_links if link['id'] in top_ids]

    finally:
        await pool.close()

#----------------------------------------
import asyncio
import google.generativeai as genai
def generate_answer_from_articles(articles: list[dict], user_query: str, gemini_api_key: str) -> str:
    genai.configure(api_key=gemini_api_key)

    model = genai.GenerativeModel("gemini-1.5-flash")

    # Gộp nội dung các bài viết
    combined_content = "\n\n".join(
        f"- {a['title']}:\n{a['content']}" for a in articles if a.get("content")
    )

    prompt = f"""
Bạn là một trợ lý AI chuyên phân tích nội dung báo chí. 
Dưới đây là các bài viết liên quan đến truy vấn: "{user_query}". 
Hãy tóm tắt và trả lời truy vấn này dựa trên nội dung:

{combined_content}

Câu trả lời:
""".strip()

    response = model.generate_content(prompt)
    return response.text.strip()

async def main():
    import dotenv
    dotenv.load_dotenv()

    db_url = os.getenv("DATABASE_URL")
    jina_ep = os.getenv("JINA_API_KEY")
    user_query = input("Nhập câu truy vấn của bạn: ")

    # Gọi xử lý truy vấn
    results = await process_user_query(db_url, user_query, jina_ep)

    # Gọi scrape (đã là async)
    articles = await scrape_from_urls(results)

    # # Ví dụ: in ra
    # print(f"✅ Đã thu thập {len(articles)} bài viết.")
    # for a in articles:
    #     print(f"📝 {a['title']} - {a['content']}")
    gemini_api_key = os.getenv("GOOGLE_API_KEY")
    if not gemini_api_key:
        print("❌ Thiếu GOOGLE_API_KEY")
        return

    answer = generate_answer_from_articles(articles, user_query, gemini_api_key)
    print("\n🤖 Câu trả lời từ Gemini:")
    print(answer)

# import time
if __name__ == "__main__":
    # time = time.s
    asyncio.run(main())
