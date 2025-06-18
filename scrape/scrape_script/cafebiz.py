import json
import time
import re
from datetime import datetime
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, BrowserConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
import pytz
import logging

import contextlib
import os
import sys

@contextlib.contextmanager
def suppress_output():
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = devnull
        sys.stderr = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

def convert_vn_time_to_local(vn_time_str):
    """
    Chuyển chuỗi thời gian kiểu Việt Nam (24h) thành datetime với timezone Asia/Ho_Chi_Minh.
    Tự động bỏ AM/PM nếu có.
    """
    try:
        cleaned_str = re.sub(r'\s*(AM|PM)', '', vn_time_str, flags=re.IGNORECASE).strip()
        vn_time = datetime.strptime(cleaned_str, '%d/%m/%Y %H:%M')
        vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        return vn_tz.localize(vn_time)
    except (ValueError, TypeError) as e:
        print(f"❌ Lỗi chuyển đổi thời gian '{vn_time_str}': {e}")
        return None


async def scrape_cafebiz_article(url):
    schema = {
        "name": "Article",
        "baseSelector": "div.content#mainDetail",
        "fields": [
            {"name": "title", "selector": "h1.title", "type": "text"},
            {"name": "time", "selector": "div.timeandcatdetail span.time", "type": "text"},
            {"name": "author", "selector": "p.p-author strong.detail-author", "type": "text"},
            {"name": "content", "selector": "div.detail-content", "type": "text"}
        ]
    }

    browser_config = BrowserConfig(
        browser_type="chromium",
        headless=True,
        viewport_width=1280,
        viewport_height=720,
        extra_args=["--disable-extensions"],
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        wait_for_article = """js:() => {
            return document.querySelector('div.content#mainDetail') !== null;
        }"""

        await crawler.arun(
            url=url,
            config=CrawlerRunConfig(
                wait_for=wait_for_article,
                session_id="cafebiz",
                cache_mode=CacheMode.BYPASS
            )
        )

        result = await crawler.arun(
            url=url,
            config=CrawlerRunConfig(
                extraction_strategy=JsonCssExtractionStrategy(schema),
                session_id="cafebiz",
                cache_mode=CacheMode.BYPASS
            )
        )

        article = None
        if result and result.extracted_content:
            try:
                article = json.loads(result.extracted_content)[0]
                if "time" in article:
                    parsed_time = convert_vn_time_to_local(article["time"])
                    article["time"] = parsed_time.isoformat() if parsed_time else None

                article["href"] = url
                article["source"] = "Cafebiz"
            except Exception as e:
                print(f"❌ Lỗi xử lý dữ liệu Cafebiz: {e}")
        else:
            print("❌ Không trích xuất được nội dung từ Cafebiz")

        return article

