import os
from dotenv import load_dotenv
import pandas as pd
import asyncpg
import re
from datetime import timezone, timedelta, datetime
from zoneinfo import ZoneInfo

def parse_article_time_fireant(date_time_str):
    vn_tz = ZoneInfo("Asia/Ho_Chi_Minh")
    now = datetime.now(vn_tz)  # ✅ Thời gian hiện tại theo múi giờ Việt Nam

    # ✅ ISO 8601 dạng: 2025-06-13T08:30:00.000000Z
    try:
        if "T" in date_time_str and "Z" in date_time_str:
            dt_utc = datetime.strptime(date_time_str, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
            return dt_utc.astimezone(vn_tz)  # ✅ Chuyển về giờ Việt Nam
    except ValueError:
        pass

    # ✅ "Hôm nay hh:mm"
    if "Hôm nay" in date_time_str:
        match = re.search(r'(\d{1,2}):(\d{2})', date_time_str)
        if match:
            hour, minute = int(match.group(1)), int(match.group(2))
            local_time = datetime(now.year, now.month, now.day, hour, minute, tzinfo=vn_tz)
            return local_time
        return now.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=vn_tz)

    # ✅ "x tiếng trước"
    if "tiếng" in date_time_str:
        match = re.search(r'(\d+)', date_time_str)
        hours_ago = int(match.group(1)) if match else 0
        local_time = now - timedelta(hours=hours_ago)
        return local_time

    # ✅ "x phút trước"
    if "phút" in date_time_str:
        match = re.search(r'(\d+)', date_time_str)
        minutes_ago = int(match.group(1)) if match else 0
        local_time = now - timedelta(minutes=minutes_ago)
        return local_time

    return None

async def create_links_tables(pool):
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS links (
                link_id SERIAL PRIMARY KEY,
                url TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                description TEXT,`
                inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
async def save_links_to_db(pool, links, source):
    if not links:
        print("⚠️ Không có bài viết nào để lưu.")
        return

    insert_query = """
        INSERT INTO links (url, title, description, source)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (url) DO NOTHING;
    """

    async with pool.acquire() as conn:
        for link in links:
            try:
                # time = link.get("time")
                # if isinstance(time, str):
                #     parsed_time = parse_article_time_fireant(time)
                await conn.execute(
                    insert_query,
                    link.get("href"),
                    link.get("title"),
                    link.get("description"),
                    source
                )
                print(f"✅ Inserted: {link['title']}")
            except Exception as e:
                print(f"❌ Error inserting article {link.get('href')}: {e}")
                
async def write_links_to_db(links, db_url, create_table=False, source=None):
    if not db_url:
        raise ValueError("db_url is not set")
    pool = await asyncpg.create_pool(db_url)
    if create_table:
        await create_links_tables(pool)

    print(f"📝 Tổng số bài viết cần lưu: {len(links)}")
    await save_links_to_db(pool, links, source)
    await pool.close()
    
