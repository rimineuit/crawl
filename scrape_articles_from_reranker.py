from urllib.parse import urlparse
import asyncio

from scrape.scrape_script.fireant import scrape_fireant_article
from scrape.scrape_script.cafebiz import scrape_cafebiz_article
from scrape.scrape_script.cafef import scrape_cafef_article
from scrape.scrape_script.vietstock import scrape_vietstock_article

SCRAPE_FUNC_MAP = {
    "fireant.vn": scrape_fireant_article,
    "cafebiz.vn": scrape_cafebiz_article,
    "cafef.vn": scrape_cafef_article,
    "vietstock.vn": scrape_vietstock_article,
}


async def scrape_from_urls(article_list):
    """
    article_list: list các dict có key 'url'
    Trả về: list các dict chứa article đã scrape
    """
    tasks = []

    for item in article_list:
        url = item.get("href")
        if not url:
            continue

        domain = urlparse(url).netloc.lower()
        scrape_func = None

        for d, func in SCRAPE_FUNC_MAP.items():
            if d in domain:
                scrape_func = func
                break

        if scrape_func:
            tasks.append(scrape_func(url))
        else:
            print(f"⚠️ Không có scraper cho domain '{domain}'")

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Lọc lỗi
    articles = []
    for res in results:
        if isinstance(res, Exception):
            print(f"❌ Lỗi khi scrape: {res}")
        elif res:
            articles.append(res if isinstance(res, dict) else res[0])

    return articles
