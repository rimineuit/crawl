import asyncio
import json
import logging
from datetime import datetime, timedelta
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, BrowserConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
import re
from utils import check_article_existed_in_db

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import logging
import re


def get_time():
    """Return the current hour and minute as a tuple."""
    now = datetime.now()
    return now.hour, now.minute

from datetime import datetime, timedelta, timezone

def parse_article_time(date_time_str):
    """Parse time string and return UTC datetime if it's from today, else None."""
    now = datetime.now()
    if "HOURS" in date_time_str:
        match = re.search(r'(\d+)', date_time_str)
        hours_ago = int(match.group(1)) if match else 0
        local_time = now - timedelta(hours=hours_ago)
        return local_time.astimezone(timezone.utc)
    # Các dạng như "Hôm qua", "2 ngày trước" sẽ bị bỏ qua
    return None

async def visit_link_vietstock(link):
    browser_config = BrowserConfig(
        browser_type="chromium",
        headless=True,
        extra_args=["--disable-extensions"],
    )

    at_least_on_article = """js:() => {
        return document.querySelector('div.Card-textContent') !== null;
    }"""
    schema = {
        "name": "Article",
        "baseSelector": "div.Card-textContent",
        "fields": [
            {"name": "title", "selector": "div.Card-titleContainer a", "type": "text"},
            {"name": "href", "selector": "div.Card-titleContainer a", "type": "attribute", "attribute": "href"},
            {"name": "description", "selector": "", "type": "text"},
            {"name": "time", "selector": "span.Card-time", "type": "text"}
        ]
        }
    data = []
    async with AsyncWebCrawler(config=browser_config) as crawler:
        await crawler.arun(
            url=link,
            config=CrawlerRunConfig(
                session_id="cnbc_session",
                cache_mode=CacheMode.BYPASS,
                wait_for=at_least_on_article
            )
        )
        result = await crawler.arun(
            url=link,
            config=CrawlerRunConfig(
                session_id="cnbc_session",
                cache_mode=CacheMode.BYPASS,
                extraction_strategy=schema,
                js_only=True
            )
        )
        
        articles = json.loads(result.extracted_content)
        
        
        
        
        