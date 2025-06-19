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

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import re
import logging

from datetime import datetime
from zoneinfo import ZoneInfo
import logging

def check_date_time(date_time_str: str) -> datetime | None:
    """
    Parse chuỗi ngày tháng dạng 'dd/mm/yyyy' và trả về đối tượng datetime 
    với timezone Asia/Ho_Chi_Minh nếu hợp lệ và trong ngày hôm nay.
    """
    vn_tz = ZoneInfo("Asia/Ho_Chi_Minh")
    now = datetime.now(vn_tz)

    try:
        date_time_str = date_time_str.strip()

        # Trường hợp: "dd/mm/yyyy"
        try:
            article_time = datetime.strptime(date_time_str, "%d/%m/%Y")
            article_time = article_time.replace(tzinfo=vn_tz)
            if article_time.date() == now.date():
                return article_time
            else:
                return None
        except ValueError:
            logging.warning(f"⚠️ Unrecognized date format: '{date_time_str}'")
            return None

    except Exception as e:
        logging.warning(f"⚠️ Error parsing date string '{date_time_str}': {e}")
        return None
    
    
async def visit_link_vietstock(link):
    browser_config = BrowserConfig(
        browser_type="chromium",
        headless=True,
        extra_args=["--disable-extensions"],
    )
    at_least_on_article = """js:() => {
        return document.querySelector('div.container div.padding-bottom-30 div.row div.col-lg-8 section.scroll-content div.single_post') !== null;
    }"""
    next_page_script = """
        btn = document.querySelector("ul.pagination li.pagination-page.next a");
        if (btn) {
            btn.scrollIntoView({ behavior: 'smooth', block: 'center' });
            setTimeout(() => {
                btn.click();
            }, 500); // Chờ 500ms
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
        # print("Đã xuất hiện")
        schema = {
            "name": "Article",
            "baseSelector": "div.container div.padding-bottom-30 div.row div.col-lg-8 section.scroll-content div.single_post",
            "fields": [
                {"name": "title", "selector": "div.single_post_text.head-h h4 a", "type": "text"},
                {"name": "href", "selector": "div.single_post_text.head-h h4 a", "type": "attribute", "attribute": "href"},
                {"name": "description", "selector": "", "type": "text"},
                {"name": "time", "selector": "div.img_wrap p", "type": "text"}
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
        if not await check_article_existed_in_db(f"https://vietstock.vn{data[-1].get('href','')}"):
            while check_date_time(data[-1].get("time","")):
                result = await crawler.arun(
                url=link,
                config=CrawlerRunConfig(
                    session_id="vietstock_session",
                    cache_mode=CacheMode.BYPASS,
                    js_only=True,
                    extraction_strategy=JsonCssExtractionStrategy(schema),
                    js_code=next_page_script,
                    wait_for=at_least_on_article
                )
            )
                if await check_article_existed_in_db(f"https://vietstock.vn{data[-1].get('href','')}"):
                    break
                data.extend(json.loads(result.extracted_content))
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
                # "description": item.get("description", "").strip(),
                "published_at": parsed_time.isoformat(),
                "source": "VietStock"
            })
            
        except Exception as e:
            print(f"[⚠️] Error parsing item: {e}")
            continue

    return articles
        

    