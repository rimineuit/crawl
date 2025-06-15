import asyncio
import os
import csv
from datetime import datetime
from urllib.parse import urlparse
from playwright.async_api import async_playwright, TimeoutError
from playwright.sync_api import sync_playwright, TimeoutError
import logging
from time import sleep

from datetime import datetime
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

def check_if_need_viewmore(page):
    times = page.locator("div.Card-textContent span.Card-time")
    count =  times.count()
    print(f"Number of articles found: {count}")
    if count == 0:
        return False
    last_time = times.nth(count - 1).inner_text()
    print(last_time)
    if parse_article_time(last_time) is None:
        print("No valid time found, stopping click.")
        return False
    return True

            
def visit_link_cnbc(link, browser, max_retries=3):
    results = []
    page = browser.new_page()

    for attempt in range(1, max_retries + 1):
        try:
            logging.info(f"Attempt {attempt}/{max_retries}: Accessing {link}")
            page.goto(link, wait_until="domcontentloaded", timeout=15000)

            while check_if_need_viewmore(page):
                logging.info(f"Click to load more articles...")
                page.locator("div", has_text="Load More").click()
                page.wait_for_timeout(300)
            results.extend(get_articles_from_page(page))
            break
        except TimeoutError as te:
            logging.error(f"Timeout: {te}")
            if attempt == max_retries:
                break
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            if attempt == max_retries:
                break
        finally:
            if attempt == max_retries or results:
                page.close()

    return results

def get_articles_from_page(page):
    """Extract articles from a page."""
    results = []
    article_locator = page.locator('div.Card-textContent')
    count = article_locator.count()

    for i in range(count):
        article = article_locator.nth(i)
        try:
            if page.locator("div.Card-pro"):
                continue  # Skip sponsored articles
            time_text = article.locator("span.Card-time").inner_text()
            post_time = parse_article_time(time_text)
            if not post_time:
                continue

            a_tag = article.locator("div.Card-titleContainer a")
            href = a_tag.get_attribute("href") or ""
            title = a_tag.inner_text() or "No title"

            description = ""

            results.append({
                "title": title,
                "href": f"{href}" if href else "",
                "description": description,
                "time": post_time.isoformat()
            })
        except Exception as e:
            logging.warning(f"Error processing article {i}: {e}")
            continue
    for item in results:
        logging.info(f"Found article: {item['title']}")
    return results


