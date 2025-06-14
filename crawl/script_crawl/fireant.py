import asyncio
import time
import json
import re
from datetime import datetime, timedelta, timezone
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, BrowserConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from zoneinfo import ZoneInfo

def parse_article_time(date_time_str):
    vn_tz = ZoneInfo("Asia/Ho_Chi_Minh")
    now = datetime.now(vn_tz)  # ✅ Thời gian hiện tại theo múi giờ Việt Nam


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


async def visit_link_fireant(link):
    # JavaScript to check for "Để sau" button.
    check_button_script = """js:() => {
        return Array.from(document.querySelectorAll('button')).some(
            btn => btn.textContent.trim() === "Để sau"
        );
    }"""

    # JavaScript to click "Để sau" button and scroll until first articles appear.
    script_to_go_to_first_link = """
    new Promise(resolve => {
        // Click "Để sau" button if it exists
        const clickButton = () => {
            const buttons = document.querySelectorAll('button');
            for (let btn of buttons) {
                if (btn.textContent.trim() === 'Để sau') {
                    btn.click();
                    return true;
                }
            }
            return false;
        };

        let attempts = 0;
        const maxAttempts = 20;
        // Scroll until meet article index 0
        const tryScroll = () => {
            // If articles are found, resolve
            if (document.querySelector('div.mt-5 div.w-full div[data-index="0"]')) {
                resolve();
                return;
            }

            // Scroll down
            window.scrollBy(0, window.innerHeight/2);

            attempts++;
            if (attempts >= maxAttempts) {
                resolve();
                return;
            }

            setTimeout(tryScroll, 1000);
        };

        // Try to click button first
        const buttonClicked = clickButton();
        
        // Start scrolling after a short delay to ensure button click is processed
        setTimeout(tryScroll, buttonClicked ? 1000 : 500);
    });
    """
    
    wait_for_articles = """js:() => {
        return document.querySelector('div.mt-5 div.w-full div[data-index="0"]') !== null;
    }"""

    schema = {
        "name": "Article",
        "baseSelector": "div.mt-5 div.w-full div[data-index]",
        "fields": [
            {"name": "title", "selector": "div div.flex div.flex-1 div.mb-2 a", "type": "text"},
            {"name": "href", "selector": "div div.flex div.flex-1 div.mb-2 a", "type": "attribute","attribute": "href"},
            {"name": "description", "selector": "div.mb-2.max-sm.line-clamp-2", "type": "text"},
            {"name": "time_publish", "selector": "div div.flex.flex-1 div.flex-1 div.flex.flex-row div.flex-1 span.text-gray-400","type": "text"},
        ]
    }

    browser_config = BrowserConfig(
        browser_type="chromium",
        headless=True,
        extra_args=["--disable-extensions"],
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        start = time.time()
        
        # First, check if the button "Để sau" exists and click it
        await crawler.arun(
            url=link,
            config=CrawlerRunConfig(
                wait_for=check_button_script,
                session_id='rimine',
                cache_mode=CacheMode.BYPASS
            )
        )

        # Then execute main script to click button and scroll until article index 0 on the screen
        first_article = await crawler.arun(
            url=link,
            config=CrawlerRunConfig(
                js_code=script_to_go_to_first_link,
                wait_for=wait_for_articles,
                session_id='rimine',
                extraction_strategy=JsonCssExtractionStrategy(schema),
                cache_mode=CacheMode.BYPASS,
                js_only=True
            )
        )
        
        data = []
        data.extend(json.loads(first_article.extracted_content))
        # Vòng lặp while để lấy tất cả những bài viết trong ngày
        while True:
            js_code="""
            new Promise(resolve => {
                window.scrollBy(0, window.innerHeight);
            });
            """
            contents = await crawler.arun(
                url=link,
                config=CrawlerRunConfig(
                    js_code=js_code,
                    # wait_for="js:() => document.querySelectorAll('div[data-index]').length >= 5",
                    session_id='rimine',
                    extraction_strategy=JsonCssExtractionStrategy(schema),
                    js_only=True,
                    cache_mode=CacheMode.BYPASS
                )
            )
            await asyncio.sleep(0.5)
            articles = json.loads(contents.extracted_content)
            data.extend(articles)
            # Check if the last article is not in today
            if parse_article_time(articles[-1].get("time_publish","")) == None:
                print(parse_article_time(articles[-1].get("time_publish","")))
                print("Last article is not in today!")
                break
            
            
        end = time.time()
        print(f"✅ Crawl done in {round(end - start, 2)}s")

        articles = []
    
        vn_tz = ZoneInfo("Asia/Ho_Chi_Minh")
        now = datetime.now(vn_tz)
        today = now.date()

        for item in data:
            try:
                time_str = item.get("time_publish", "")
                parsed_time = parse_article_time(time_str)
                if not parsed_time:
                    continue

                # ✅ Bỏ qua nếu không phải bài hôm nay
                if parsed_time.date() != today:
                    continue

                articles.append({
                    "title": item.get("title", "").strip(),
                    "href": f"https://fireant.vn{item.get('href', '')}",
                    "description": item.get("description", "").strip(),
                    "time": time_str
                })
            except Exception as e:
                print(f"[⚠️] Error parsing item: {e}")
                continue


        return articles

