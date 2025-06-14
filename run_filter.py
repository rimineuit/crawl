# run_filter.py
import sys
import asyncio
import os
from find_match_keywords_and_scrape import filter_links_by_keywords
from dotenv import load_dotenv
import json

async def main(keywords_file="key_words.txt"):
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    matched_links = await filter_links_by_keywords(db_url, key_words_path=keywords_file)
    json_str = json.dumps(matched_links, ensure_ascii=False, indent=2)
    sys.stdout.buffer.write(json_str.encode('utf-8'))
    # print("Lenght:", len(matched_links))
if __name__ == "__main__":
    keywords_file = sys.argv[1]
    asyncio.run(main(keywords_file))
