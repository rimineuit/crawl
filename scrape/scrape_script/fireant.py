import sys
import os

# Thêm thư mục gốc của project vào sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from zoneinfo import ZoneInfo  # Python 3.9+
import asyncio
import time
import json
import re
from datetime import datetime, timedelta, timezone
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, BrowserConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
# from crawl_and_scraper.scrape_articles.scrape_fireant import scrape_fireant_requests, write_to_db
# from crawl_and_scraper.utils import get_key_words, matching_links, save_to_csv, check_and_deduplicate_csv, get_domain_links
from datetime import datetime, timedelta, timezone
import re
from dotenv import load_dotenv
load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')


from datetime import datetime, timezone

def convert_vn_time_to_utc(time_str: str) -> datetime | None:
    """
    Nhận chuỗi thời gian ISO 8601 (ví dụ '2025-06-13T09:44:00.000Z') và trả về datetime UTC có tzinfo.
    """
    if not time_str:
        return None

    try:
        # Xử lý hậu tố 'Z' (Z = Zulu time = UTC)
        if time_str.endswith('Z'):
            time_str = time_str.replace('Z', '+00:00')
        
        dt_utc = datetime.fromisoformat(time_str)
        return dt_utc  # Đã có tzinfo = UTC
    except Exception as e:
        print(f"❌ Lỗi convert thời gian ISO 8601: {e}")
        return None

    
async def scrape_fireant_article(link):
    schema_article = {
        "name": "Article",
        "baseSelector": "div.flex.gap-4.w-full div.flex-1.w-full.border-gray-100 div.flex",
        "fields": [
            {"name": "title", "selector": "div.mt-3.mb-5.text-3xl.font-semibold", "type": "text"},
            {"name": "time", "selector": "div.line-clamp-2 span:nth-of-type(2) time", "type": "attribute", "attribute": "datetime"},
            {"name": "author", "selector": "a.line-clamp-1 div.line-clamp-1", "type": "text"},
            {"name": "content", "selector": "div.pt-5.text-lg[id='post_content']", "type": "text"},
        ]
    }

    browser_config = BrowserConfig(
        browser_type="chromium",
        headless=False,
        extra_args=["--disable-extensions"],
        viewport_width=1320,
        viewport_height=720,
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        start = time.time()

        wait_for_articles = """js:() => {
            return document.querySelector('div.flex.gap-4.w-full div.flex-1.w-full.border-gray-100 div.flex') !== null;
        }"""
        
        await crawler.arun(
            url=link,
            config=CrawlerRunConfig(
                wait_for=wait_for_articles,
                session_id='rimine',
                cache_mode=CacheMode.BYPASS
            )
        )

        # Scrape nội dung article
        result = await crawler.arun(
            url=link,
            config=CrawlerRunConfig(
                extraction_strategy=JsonCssExtractionStrategy(schema_article),
                session_id='rimine',
                cache_mode=CacheMode.BYPASS
            )
        )

        article = None
        if result:
            try:
                article = json.loads(result.extracted_content)[0]

                # ✅ Chuyển đổi time sang UTC datetime object
                if "time" in article:
                    converted_time = convert_vn_time_to_utc(article["time"])
                    if converted_time:
                        article["time"] = converted_time
                    else:
                        print(f"⚠️ Không thể chuyển đổi thời gian: {article['time']}")
                        article["time"] = None

                print("✅ Scrape article success")
            except Exception as e:
                print(f"❌ Error parsing article result: {e}")
                article = None
        else:
            print("❌ Scrape article fail")

        return article

    