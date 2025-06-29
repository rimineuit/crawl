import sys
import os

# Thêm thư mục gốc project vào sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from dotenv import load_dotenv 
load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
import asyncio
from crawl.script_crawl.cafef import visit_link_cafef
from insert_links_to_db import write_links_to_db
from utils import get_domain_links

async def main():
    urls = get_domain_links("./crawl/domain_links/cafef.txt")
        
    for url in urls:
        articles = await visit_link_cafef(url)  # truyền context hoặc browser tùy bạn thiết kế
        print(f"Crawled {len(articles)} articles from {url}")
        await write_links_to_db(articles, DATABASE_URL, source="CafeF")
    
if __name__ == "__main__":
    asyncio.run(main())
