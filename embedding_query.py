import requests
import os
import sys
# Thêm thư mục gốc của project vào sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


async def embedding_query_with_jina(query: str, api_key: str) -> list[float]:
    url = 'https://api.jina.ai/v1/embeddings'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    data = {
        "model": "jina-embeddings-v3",
        "task": "retrieval.query",
        "dimensions": 768,
        "input": [query]
    }

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()

    embedding = response.json()["data"][0]["embedding"]
    return embedding

import asyncio
import json


if __name__ == "__main__":
    import dotenv
    dotenv.load_dotenv()

    jina_ep = os.getenv("JINA_API_KEY")
    if len(sys.argv) < 2:
        print("❌ Cần truyền truy vấn.")
        sys.exit(1)

    query = sys.argv[1]
    
    result = asyncio.run(embedding_query_with_jina(query, jina_ep))
    output = {"response": result }
    print(json.dumps(output, ensure_ascii=False))