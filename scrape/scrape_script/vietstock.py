from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, BrowserConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from datetime import datetime
import time
import json
import re


def convert_vn_time_to_utc(vn_time_str):
    """
    Chuyển chuỗi thời gian có định dạng 'dd-mm-YYYY HH:MM:SS+07:00' thành datetime với tzinfo=UTC+7.
    """
    try:
        # Parse thành datetime có tzinfo (UTC+7)
        vn_time = datetime.strptime(vn_time_str, '%d-%m-%Y %H:%M:%S%z')
        return vn_time  # giữ nguyên UTC+7
    except (ValueError, TypeError) as e:
        print(f"❌ Error converting time '{vn_time_str}': {e}")
        return None


async def scrape_vietstock_article(link):
    schema_article = {
        "name": "Article",
        "baseSelector": "div.row.scroll-content",
        "fields": [
            {"name": "title", "selector": "h1.article-title", "type": "text"},
            {"name": "time", "selector": "div.dateNewBlock span.datenew", "type": "text"},
            {"name": "author", "selector": "p.pAuthor a", "type": "text"},
            {"name": "content", "selector": "div#vst_detail", "type": "text"},
        ]
    }

    browser_config = BrowserConfig(
        browser_type="chromium",
        headless=True,
        extra_args=["--disable-extensions"],
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        wait_for_selector = """js:() => {
            return document.querySelector('div.row.scroll-content') !== null;
        }"""

        await crawler.arun(
            url=link,
            config=CrawlerRunConfig(
                wait_for=wait_for_selector,
                session_id='vietstock-session',
                cache_mode=CacheMode.BYPASS
            )
        )

        result = await crawler.arun(
            url=link,
            config=CrawlerRunConfig(
                extraction_strategy=JsonCssExtractionStrategy(schema_article),
                session_id='vietstock-session',
                cache_mode=CacheMode.BYPASS
            )
        )

        article = None
        if result:
            try:
                article = json.loads(result.extracted_content)[0]
                if "time" in article:
                    converted_time = convert_vn_time_to_utc(article["time"])
                    if converted_time:
                        article["time"] = converted_time
                    else:
                        article["time"] = None

                if "source" not in article or not article["source"]:
                    article["source"] = "Vietstock"

                if "author" not in article or not article["author"]:
                    article["author"] = "Unknown"

                article["href"] = link

                print("✅ Scrape vietstock article success")
            except Exception as e:
                print(f"❌ Error parsing article result: {e}")
                article = None
        else:
            print("❌ Failed to scrape article content")

        return article
