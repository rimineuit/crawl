import requests


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


