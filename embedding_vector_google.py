import asyncio
import os
import dotenv
import requests
import asyncpg

dotenv.load_dotenv()

db_url = os.getenv("DATABASE_URL")
google_access_token = os.getenv("GOOGLE_API_KEY")
project_id = os.getenv("GOOGLE_PROJECT_ID")  # Lấy Project ID từ .env

BATCH_SIZE = 50

async def fetch_links_without_embedding(pool, batch_size):
    """Lấy batch các link chưa có embedding."""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, content
            FROM articles
            WHERE embedding IS NULL
            LIMIT $1
        """, batch_size)
        return [
            {
                'id': row['id'],
                'text': (row['content'] or '')
            }
            for row in rows
        ]

async def embed_links_with_google(links, access_token, project_id):
    """Gửi văn bản tới Google Text Embedding 004 API để lấy embedding."""
    url = f'https://us-central1-aiplatform.googleapis.com/v1/projects/{project_id}/locations/us-central1/publishers/google/models/text-embedding-004:predict'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    documents = [link['text'] for link in links]
    data = {
        "instances": [{"content": doc} for doc in documents],
        "parameters": {"task_type": "RETRIEVAL_DOCUMENT"}
    }

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    json_data = response.json()
    
    embeddings = []
    for idx, item in enumerate(json_data["predictions"]):
        embedding = item["embeddings"]["values"]
        link_id = links[idx]["id"]
        embeddings.append((link_id, embedding))
    return embeddings

def list_to_pgvector(v):
    """Chuyển danh sách số thành định dạng pgvector."""
    return f'[{", ".join(f"{x:.8f}" for x in v)}]'

async def save_embeddings_to_db(pool, embeddings):
    """Lưu embedding vào database."""
    async with pool.acquire() as conn:
        await conn.executemany(
            "UPDATE articles SET embedding = $1 WHERE id = $2",
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
            embeddings = await embed_links_with_google(links, google_access_token, project_id)
            await save_embeddings_to_db(pool, embeddings)
            await asyncio.sleep(1)  # Tránh gọi API quá nhanh
            total += len(embeddings)
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            break  # Có thể thêm logic retry nếu cần

    await pool.close()

if __name__ == "__main__":
    asyncio.run(process_all_links())