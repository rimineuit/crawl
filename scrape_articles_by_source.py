import sys
import asyncio
from urllib.parse import urlparse

from scrape.scrape_script.fireant import scrape_fireant_article
from scrape.scrape_script.cafebiz import scrape_cafebiz_article
from scrape.scrape_script.cafef import scrape_cafef_article
from scrape.scrape_script.vietstock import scrape_vietstock_article

SCRAPE_FUNC_MAP = {
    "Fireant": scrape_fireant_article,
    "CafeBiz": scrape_cafebiz_article,
    "CafeF": scrape_cafef_article,
    "VietStock": scrape_vietstock_article,
}


async def main():
    if len(sys.argv) < 4:
        print("⚠️ Dùng: python script.py <url> <source> <id>")
        return

    url = sys.argv[1]
    source = sys.argv[2]
    id = sys.argv[3]
    
    scrape_func = SCRAPE_FUNC_MAP.get(source)

    if not scrape_func:
        print(f"❌ Source không hợp lệ: '{source}'. Hỗ trợ: {list(SCRAPE_FUNC_MAP.keys())}")
        return

    try:
        article = await scrape_func(url)
        article["id"] = id  # ✅ Thêm ID vào dict kết quả
        import json
        print(json.dumps(article, ensure_ascii=False))  # ✅ In ra JSON hợp lệ

    except Exception as e:
        print(f"❌ Lỗi khi scrape: {e}")


if __name__ == "__main__":
    asyncio.run(main())
