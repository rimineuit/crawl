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
# from crawl_and_scraper.utils import get_latest_csv_file, create_tables, save_articles_to_db
# Load biến môi trường
import re
from datetime import datetime
import pytz

def convert_vn_time_to_local(vn_time_str):
    """
    Chuyển chuỗi thời gian kiểu Việt Nam (24h) thành datetime với timezone Asia/Ho_Chi_Minh.
    Tự động bỏ AM/PM nếu có.
    """
    try:
        # Bỏ AM/PM nếu có, không phân biệt hoa thường
        cleaned_str = re.sub(r'\s*(AM|PM)', '', vn_time_str, flags=re.IGNORECASE).strip()

        # Parse theo định dạng 24h
        vn_time = datetime.strptime(cleaned_str, '%d/%m/%Y %H:%M')

        # Gán timezone
        vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        return vn_tz.localize(vn_time)

    except (ValueError, TypeError) as e:
        print(f"❌ Lỗi chuyển đổi thời gian '{vn_time_str}': {e}")
        return None

def scrape_cafebiz_requests(url):
    """
    Trích xuất thông tin bài viết từ trang Cafebiz.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    articles = []

    # Tìm phần chứa nội dung bài viết
    article = soup.select_one('div.content#mainDetail')
    if not article:
        print(f"⚠️ Không tìm thấy phần nội dung bài viết trong {url}")
        return []

    # Trích xuất tiêu đề
    title_tag = article.select_one('h1.title')
    if not title_tag:
        print(f"⚠️ Không tìm thấy tiêu đề trong {url}")
        return []
    title = title_tag.get_text(strip=True)

    # Trích xuất thời gian
    time_tag = article.select_one('div.timeandcatdetail span.time')
    time = time_tag.get_text(strip=True) if time_tag else None
    if time:
        time = convert_vn_time_to_local(time)
        if not time:
            print(f"❌ Không thể chuyển đổi thời gian: {time_tag.get_text(strip=True)}")
            return []

    # Trích xuất tác giả
    author_tag = article.select_one('p.p-author strong.detail-author')
    author = author_tag.get_text(strip=True) if author_tag else "Unknown"

    # Trích xuất nội dung
    content_tag = article.select_one('div.detail-content')
    content = content_tag.get_text(strip=True, separator=' ') if content_tag else "No content available"

    # Thêm bài viết vào danh sách
    article = {
        "title": title,
        "href": url,
        "time": time,
        "source": "Cafebiz",
        "content": content,
        "author": author,
    }
    if not article:
        print(f"⚠️ Không tìm thấy bài viết nào trong {url}")
    return article