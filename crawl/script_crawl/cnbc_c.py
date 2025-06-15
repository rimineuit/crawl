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


import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

def parse_article_time(date_time_str: str):
    """
    Parse relative time strings (e.g., '2 hours ago', '30 minutes ago', etc.)
    and return a datetime object in UTC+7 timezone.
    If the string doesn't match, return None.
    """

    date_time_str = date_time_str.strip().lower()
    now = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))

    # Regex pattern: e.g. "2 hours ago", "30 mins ago", "an hour ago"
    hour_match = re.search(r"(\d+|an)\s*hour", date_time_str)
    minute_match = re.search(r"(\d+|a)\s*min", date_time_str)

    if hour_match:
        val = hour_match.group(1)
        hours = 1 if val in ["an"] else int(val)
        local_time = now - timedelta(hours=hours)
        return local_time

    elif minute_match:
        val = minute_match.group(1)
        minutes = 1 if val in ["a"] else int(val)
        local_time = now - timedelta(minutes=minutes)
        return local_time

    return None


async def visit_link_cnbc(link):
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
        
        data = json.loads(result.extracted_content)
        articles = []
        
        for article in data:
            
        
        
        
        
        
        
        