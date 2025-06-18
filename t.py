import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz
import json
import re
import sys

def convert_vn_time_to_local(vn_time_str):
    try:
        cleaned_str = re.sub(r'\s*(AM|PM)', '', vn_time_str, flags=re.IGNORECASE).strip()
        vn_time = datetime.strptime(cleaned_str, '%d/%m/%Y %H:%M')
        vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        return vn_tz.localize(vn_time)
    except (ValueError, TypeError) as e:
        print(f"❌ Lỗi chuyển đổi thời gian '{vn_time_str}': {e}")
        return None

def scrape_cafebiz_article(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        return {"error": f"Không truy cập được trang: {resp.status_code}"}

    soup = BeautifulSoup(resp.text, "html.parser")
    main = soup.select_one("div.content#mainDetail")
    if not main:
        return {"error": "Không tìm thấy nội dung chính"}

    article = {}
    title = main.select_one("h1.title")
    time_tag = main.select_one("div.timeandcatdetail span.time")
    author = main.select_one("p.p-author strong.detail-author")
    content = main.select_one("div.detail-content")

    article["title"] = title.get_text(strip=True) if title else None
    article["time"] = convert_vn_time_to_local(time_tag.get_text(strip=True))\
                        .isoformat() if time_tag else None
    article["author"] = author.get_text(strip=True) if author else None
    article["content"] = content.get_text(strip=True) if content else None
    article["href"] = url
    article["source"] = "Cafebiz"

    return article

if __name__ == "__main__":
    url = sys.argv[1]
    result = scrape_cafebiz_article(url)
    print(json.dumps(result, ensure_ascii=False))
