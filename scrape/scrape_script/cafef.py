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
# Load biến môi trường
load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

from bs4 import BeautifulSoup
import requests
from datetime import datetime
import pytz

from datetime import datetime
import pytz

def convert_vn_time_to_aware(vn_time_str):
    """
    Chuyển đổi chuỗi thời gian Việt Nam (VD: '09-06-2025 - 14:21 AM/PM') 
    thành datetime có timezone Asia/Ho_Chi_Minh.
    """
    try:
        # Làm sạch chuỗi và parse theo định dạng
        vn_time_str = vn_time_str.replace('AM', '').replace('PM',"").strip()
        vn_time = datetime.strptime(vn_time_str.strip(), '%d-%m-%Y - %H:%M')

        # Gán timezone Asia/Ho_Chi_Minh
        vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        aware_time = vn_tz.localize(vn_time)

        return aware_time  # dạng datetime có timezone
    except (ValueError, TypeError) as e:
        print(f"❌ Error converting time '{vn_time_str}': {e}")
        return None

def scrape_cafef_requests(url):
    """
    Trích xuất thông tin bài viết từ trang Cafef.
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
    article = soup.select_one('div.left_cate.totalcontentdetail')
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
    time_tag = article.select_one('span.pdate')
    time = time_tag.get_text(strip=True) if time_tag else None
    if time:
        time = convert_vn_time_to_aware(time)
        if not time:
            print(f"❌ Không thể chuyển đổi thời gian: {time_tag.get_text(strip=True)}")
            return []

    # Trích xuất tác giả
    author_tag = article.select_one('p.author')
    author = author_tag.get_text(strip=True) if author_tag else "Unknown"

    # Trích xuất nội dung
    content_tag = article.select_one('div.detail-content.afcbc-body')
    content = content_tag.get_text(strip=True, separator=' ') if content_tag else "No content available"


    # Thêm bài viết vào danh sách
    article = {
        "title": title,
        "href": url,
        "time": time,
        "source": "CafeF",
        "content": content,
        "author": author,
    }
    if not article:
        print(f"⚠️ Không tìm thấy bài viết nào trong {url}")
    return article