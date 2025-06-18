import requests
import json

# URL endpoint API của bạn
API_URL = "https://crawl-production-7cae.up.railway.app/scrape"  # sửa nếu khác

# Header, nếu cần (bắt buộc có Content-Type)
headers = {
    "Content-Type": "application/json",
    # "Authorization": "Bearer YOUR_TOKEN",  # nếu cần
}

# Body gửi lên API
payload = {
    "url": "https://vietstock.vn/2025/06/sep-cu-bamboo-airways-tro-lai-lam-pho-tong-giam-doc-737-1319078.htm",
    "source": "VietStock"
}

# Gửi request
try:
    response = requests.post(API_URL, headers=headers, json=payload)
    response.raise_for_status()
    print("✅ Response:", json.dumps(response.json(), indent=2, ensure_ascii=False))
except requests.exceptions.RequestException as e:
    print("❌ Lỗi khi gửi request:", e)
