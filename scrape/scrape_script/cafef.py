import json
import re
from datetime import datetime
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, BrowserConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
import pytz


def convert_vn_time_to_aware(vn_time_str):
    """
    Chuyển đổi chuỗi thời gian Việt Nam (VD: '09-06-2025 - 14:21 AM/PM') 
    thành datetime có timezone Asia/Ho_Chi_Minh.
    """
    try:
        vn_time_str = vn_time_str.replace('AM', '').replace('PM', '').strip()
        vn_time = datetime.strptime(vn_time_str, '%d-%m-%Y - %H:%M')
        vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        return vn_tz.localize(vn_time)
    except (ValueError, TypeError) as e:
        print(f"❌ Error converting time '{vn_time_str}': {e}")
        return None


async def scrape_cafef_article(url):
    schema = {
        "name": "Article",
        "baseSelector": "div.left_cate.totalcontentdetail",
        "fields": [
            {"name": "title", "selector": "h1.title", "type": "text"},
            {"name": "time", "selector": "span.pdate", "type": "text"},
            {"name": "author", "selector": "p.author", "type": "text"},
            {"name": "content", "selector": "div.detail-content.afcbc-body", "type": "text"}
        ]
    }

    browser_config = BrowserConfig(
        browser_type="chromium",
        headless=True,
        viewport_width=1280,
        viewport_height=720
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        await crawler.arun(
            url=url,
            config=CrawlerRunConfig(
                wait_for="js:() => document.querySelector('div.left_cate.totalcontentdetail') !== null",
                session_id="cafef",
                cache_mode=CacheMode.BYPASS
            )
        )

        result = await crawler.arun(
            url=url,
            config=CrawlerRunConfig(
                extraction_strategy=JsonCssExtractionStrategy(schema),
                session_id="cafef",
                cache_mode=CacheMode.BYPASS
            )
        )

        article = None
        if result and result.extracted_content:
            try:
                article = json.loads(result.extracted_content)[0]

                # Xử lý thời gian
                if "time" in article:
                    parsed_time = convert_vn_time_to_aware(article["time"])
                    article["time"] = parsed_time if parsed_time else None

                # Bổ sung metadata
                article["href"] = url
                article["source"] = "CafeF"

                # Xử lý nếu thiếu tác giả
                if not article.get("author"):
                    article["author"] = "Unknown"

            except Exception as e:
                print(f"❌ Lỗi xử lý dữ liệu CafeF: {e}")
        else:
            print("❌ Không trích xuất được nội dung từ CafeF")

        return article
