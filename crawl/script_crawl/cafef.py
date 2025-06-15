import asyncio
import json
import logging
from datetime import datetime, timedelta
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, BrowserConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

from utils import check_article_existed_in_db
from zoneinfo import ZoneInfo

def get_time_now():
    return datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))


def check_date_time(date_time_str):
    now = get_time_now()
    try:
        if "ngày" in date_time_str:
            return False
        elif "giờ" in date_time_str:
            hours_ago = int(date_time_str.split()[0])
            article_time = now - timedelta(hours=hours_ago)
            return article_time.date() == now.date()
        elif "phút" in date_time_str:
            minutes_ago = int(date_time_str.split()[0])
            article_time = now - timedelta(minutes=minutes_ago)
            return article_time.date() == now.date()
        return False
    except (ValueError, IndexError) as e:
        logging.warning(f"Error parsing time string '{date_time_str}': {e}")
        return False


async def visit_link_cafef(link):
    # JavaScript code: Click 'View more' until the last article is not from today
    click_view_more_until_outdated = """
    new Promise(async resolve => {
        function checkDateTime(text) {
            if (text.includes("ngày")) return false;
            if (text.includes("giờ") || text.includes("phút")) return true;
            return false;
        }

        async function autoClick() {
            let attempts = 0;
            const maxAttempts = 20;

            while (attempts < maxAttempts) {
                const times = document.querySelectorAll("div.list-news span.time.time-ago");
                if (times.length === 0) break;

                const lastTime = times[times.length - 1].innerText.trim();
                if (!checkDateTime(lastTime)) break;

                
                if (!btn) break;

                btn.scrollIntoView({behavior: 'smooth'});
                btn.click();

                await new Promise(r => setTimeout(r, 3000)); // Wait for new content
                attempts++;
            }
            resolve();
        }
        await autoClick();
    });
    """

    schema = {
        "name": "Article",
        "baseSelector": "div.tlitem.box-category-item",
        "fields": [
            {"name": "title", "selector": "h3 a", "type": "text"},
            {"name": "href", "selector": "h3 a", "type": "attribute", "attribute": "href"},
            {"name": "description", "selector": "div.knswli-right p", "type": "text"},
            {"name": "time", "selector": "span.time.time-ago", "type": "text"}
        ]
    }

    browser_config = BrowserConfig(
        browser_type="chromium",
        headless=True,
        extra_args=["--disable-extensions"],
    )
    first_script = """js:() => {
        return document.querySelector('div.tlitem.box-category-item') !== null;
    }"""

    async with AsyncWebCrawler(config=browser_config) as crawler:
        await crawler.arun(
            url=link,
            config=CrawlerRunConfig(
                session_id="cafef_session",
                cache_mode=CacheMode.BYPASS,
                wait_for=first_script
            )
        )
        # Step 1: Click 'View More' until outdated
        await crawler.arun(
            url=link,
            config=CrawlerRunConfig(
                js_code=click_view_more_until_outdated,
                session_id="cafef_session",
                js_only=True,
                cache_mode=CacheMode.BYPASS
            )
        )

        # Step 2: Extract article data
        result = await crawler.arun(
            url=link,
            config=CrawlerRunConfig(
                session_id="cafef_session",
                extraction_strategy=JsonCssExtractionStrategy(schema),
                js_only=True,
                cache_mode=CacheMode.BYPASS
            )
        )

        raw_data = json.loads(result.extracted_content)

        # Step 3: Filter today's articles
        articles = []
        for item in raw_data:
            if check_date_time(item.get("time", "")):
                articles.append({
                    "title": item.get("title", "").strip(),
                    "href": f"https://cafef.vn{item.get('href', '')}",
                    "description": item.get("description", "").strip()
                })

        return articles
