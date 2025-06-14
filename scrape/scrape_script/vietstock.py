import requests
from bs4 import BeautifulSoup
import os
import asyncio
import asyncpg
from dotenv import load_dotenv
from datetime import datetime
import pandas as pd
import glob
import requests
import pytz
from playwright.async_api import async_playwright

from bs4 import BeautifulSoup
import requests
from datetime import datetime
import pytz
from datetime import datetime
import pytz

def convert_vn_time_to_utc(vn_time_str):
    """
    Chuyển đổi thời gian định dạng Việt Nam có timezone (VD: '09-06-2025 10:00:00+07:00') sang UTC (tz-aware).
    """
    try:
        # Parse datetime có timezone từ chuỗi
        vn_time = datetime.strptime(vn_time_str, '%d-%m-%Y %H:%M:%S%z')

        # Chuyển sang UTC
        utc_time = vn_time.astimezone(pytz.UTC)

        return utc_time  # datetime object with UTC tzinfo
    except (ValueError, TypeError) as e:
        print(f"❌ Error converting time '{vn_time_str}': {e}")
        return None


async def scrape_vietstock_playwright(url):
    articles = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url, timeout=60000)
            await page.wait_for_load_state('load')

            # Scroll tới cuối trang và chờ 1s
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            await asyncio.sleep(1)

            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")

            # Optional: Lưu vào file debug
            filename = f"page_dump_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(soup.prettify())

            article = soup.select_one('div.row.scroll-content')
            if not article:
                print(f"⚠️ Không tìm thấy phần nội dung bài viết trong {url}")
                return []

            title_tag = article.select_one('h1.article-title')
            if not title_tag:
                print(f"⚠️ Không tìm thấy tiêu đề trong {url}")
                return []
            title = title_tag.get_text(strip=True)

            time_tag = article.select_one('div.dateNewBlock span.datenew')
            time = time_tag.get_text(strip=True) if time_tag else None
            if time:
                time = convert_vn_time_to_utc(time)
                if not time:
                    print(f"❌ Không thể chuyển đổi thời gian: {time_tag.get_text(strip=True)}")
                    return []

            author_tag = article.select_one('p.pAuthor a')
            author = author_tag.get_text(strip=True) if author_tag else "Unknown"

            source_tag = article.select_one('p.pSource a')
            source = source_tag.get_text(strip=True) if source_tag else "Vietstock"

            content_tag = article.select_one('div#vst_detail')
            content = content_tag.get_text(strip=True, separator=' ') if content_tag else "No content available"

            stock_tags = article.select('p.pHead a')
            stocks = [tag.get_text(strip=True) for tag in stock_tags] if stock_tags else []

            tag_tags = article.select('div.tags ul.inline li a')
            tags = [tag.get_text(strip=True) for tag in tag_tags if tag.get_text(strip=True)] if tag_tags else []

            articles.append({
                "title": title,
                "href": url,
                "time": time,
                "source": source,
                "content": content,
                "author": author,
                "stocks": stocks,
                "tags": tags
            })

        except Exception as e:
            print(f"❌ Error loading {url}: {e}")
        finally:
            await browser.close()

    return articles