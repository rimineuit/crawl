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

def check_date_time(date_time_str: str) -> bool:
    """
    Kiểm tra xem thời gian trong chuỗi có nằm trong ngày hiện tại không (giờ Việt Nam).
    Hỗ trợ các định dạng:
    - 'x giờ trước'
    - 'x phút trước'
    - 'dd/mm HH:MM'
    """
    vn_tz = ZoneInfo("Asia/Ho_Chi_Minh")
    now = datetime.now(vn_tz)

    try:
        date_time_str = date_time_str.strip().lower()

        # Trường hợp: "x giờ trước"
        if "giờ" in date_time_str:
            match = re.search(r"(\d+)\s*giờ", date_time_str)
            if match:
                hours_ago = int(match.group(1))
                article_time = now - timedelta(hours=hours_ago)
                return article_time.date() == now.date()

        # Trường hợp: "x phút trước"
        elif "phút" in date_time_str:
            match = re.search(r"(\d+)\s*phút", date_time_str)
            if match:
                minutes_ago = int(match.group(1))
                article_time = now - timedelta(minutes=minutes_ago)
                return article_time.date() == now.date()

        # Trường hợp: "dd/mm HH:MM"
        else:
            try:
                article_time = datetime.strptime(date_time_str, "%d/%m %H:%M")
                article_time = article_time.replace(year=now.year, tzinfo=vn_tz)
                return article_time.date() == now.date()
            except ValueError:
                logging.warning(f"⚠️ Unrecognized time format: '{date_time_str}'")
                return False

    except Exception as e:
        logging.warning(f"⚠️ Error parsing time string '{date_time_str}': {e}")
        return False

async def visit_link_vietstock(link):
    browser_config = BrowserConfig(
        browser_type="chromium",
        headless=True,
        extra_args=["--disable-extensions"],
    )
    at_least_on_article = """js:() => {
        return document.querySelector('div.container div.col-md-12 div.business div.single_post div.single_post_text') !== null;
    }"""
    next_page_script = """
        btn = document.querySelector("li.pagination-page.next");
        if (btn) {
            btn.click();
            }
    """
    data = []
    async with AsyncWebCrawler(config=browser_config) as crawler:
        await crawler.arun(
            url=link,
            config=CrawlerRunConfig(
                session_id="vietstock_session",
                cache_mode=CacheMode.BYPASS,
                wait_for=at_least_on_article
            )
        )
        schema = {
            "name": "Article",
            "baseSelector": "div.container div.col-md-12 div.business div.single_post div.single_post_text",
            "fields": [
                {"name": "title", "selector": "h4 a", "type": "text"},
                {"name": "href", "selector": "h4 a", "type": "attribute", "attribute": "href"},
                {"name": "description", "selector": "p.post-p", "type": "text"},
                {"name": "time", "selector": "div.row div.col-12 div.meta3 a[target='']", "type": "text"}
            ]
        }
        # Lấy các bài ở trang đầu
        result = await crawler.arun(
            url=link,
            config=CrawlerRunConfig(
                session_id="vietstock_session",
                cache_mode=CacheMode.BYPASS,
                js_only=True,
                extraction_strategy=JsonCssExtractionStrategy(schema),
            )
        )
        raw_data = json.loads(result.extracted_content)
        data.extend(raw_data)
        if not check_article_existed_in_db(raw_data[-1].get("url","")):
            while check_date_time(data[-1].get("time","")):
                result = await crawler.arun(
                url=link,
                config=CrawlerRunConfig(
                    session_id="vietstock_session",
                    cache_mode=CacheMode.BYPASS,
                    js_only=True,
                    extraction_strategy=JsonCssExtractionStrategy(schema),
                    wait_for=at_least_on_article,
                    js_code=next_page_script
                )
            )
                if check_article_existed_in_db(raw_data[-1].get("url","")):
                    break
                data.extend(json.loads(result))
    articles = []
    for item in data:
        try:
            time_str = item.get("time", "")
            parsed_time = check_date_time(time_str)
            if not parsed_time:
                continue

            articles.append({
                "title": item.get("title", "").strip(),
                "href": f"https://vietstock.vn{item.get('href', '')}",
                "description": item.get("description", "").strip(),
            })
            
        except Exception as e:
            print(f"[⚠️] Error parsing item: {e}")
            continue

    return articles
        

    