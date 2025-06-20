import asyncio
import os
import dotenv
import requests
import asyncpg

dotenv.load_dotenv()

db_url = os.getenv("DATABASE_URL")
jina_api_key = os.getenv("JINA_API_KEY")

BATCH_SIZE = 10

async def fetch_links_without_embedding(pool, batch_size):
    """Lấy batch các link chưa có embedding."""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT link_id, content
            FROM articles
            WHERE embedding IS NULL
            LIMIT $1
        """, batch_size)
        return [
            {
                'id': row['link_id'],
                'text': (row['content'] or '')
            }
            for row in rows
        ]

async def embed_links_with_jina(links, jina_api_key):
    """Gửi văn bản tới Jina API để lấy embedding."""
    url = 'https://api.jina.ai/v1/embeddings'
    print(jina_api_key)
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {jina_api_key}'
    }

    documents = [link['text'] for link in links]
    data = {
        "model": "jina-embeddings-v3",
        "task": "retrieval.passage",
        "dimensions": 768,
        "input": documents
    }

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    json_data = response.json()
    embeddings = []
    for item in json_data["data"]:
        index = item["index"]
        embedding = item["embedding"]
        link_id = links[index]["id"]
        embeddings.append((link_id, embedding))
    return embeddings

def list_to_pgvector(v):
    return f'[{", ".join(f"{x:.8f}" for x in v)}]'

async def save_embeddings_to_db(pool, embeddings):
    async with pool.acquire() as conn:
        await conn.executemany(
            "UPDATE links SET embedding = $1 WHERE link_id = $2",
            [(list_to_pgvector(embedding), link_id) for link_id, embedding in embeddings]
        )


async def process_all_links():
    """Chạy xử lý cho đến khi không còn link nào thiếu embedding."""
    pool = await asyncpg.create_pool(dsn=db_url)
    total = 0

    while True:
        links = await fetch_links_without_embedding(pool, BATCH_SIZE)
        if not links:
            print(f"✅ Hoàn tất. Tổng số links đã xử lý: {total}")
            break

        print(f"🧠 Đang xử lý {len(links)} link...")
        try:
            embeddings = await embed_links_with_jina(links, jina_api_key)
            await save_embeddings_to_db(pool, embeddings)
            total += len(embeddings)
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            break  # bạn có thể retry ở đây nếu muốn

    await pool.close()

if __name__ == "__main__":
    asyncio.run(process_all_links())