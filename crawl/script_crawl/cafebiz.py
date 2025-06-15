import asyncio
import time
import json
import re
from datetime import datetime, timedelta, timezone
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, BrowserConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from zoneinfo import ZoneInfo
import logging
from datetime import datetime
from zoneinfo import ZoneInfo  # Python 3.9+

def check_time(time_str):
    if not time_str or time_str.strip() == "":
        return False
    try:
        article_time = datetime.strptime(time_str, "%H:%M %d/%m/%Y")

        # Gán timezone giả định là Asia/Ho_Chi_Minh
        article_time = article_time.replace(tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))

        now = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))

        return article_time.date() == now.date()
    except Exception as e:
        print(f"[Lỗi] Sai định dạng thời gian hoặc zone: '{time_str}' - {e}")
        return False

    
async def visit_link_cafebiz(link):
    # JavaScript: Scroll để hiển thị nút "Xem thêm"
    scroll_to_load_view_more = """
    new Promise(resolve => {
        const footer = document.querySelector('div.load-more-cell');
        if (!footer) {
            resolve(); // Không có footer thì kết thúc
            return;
        }

        let attempts = 0;
        const maxAttempts = 10000;

        const waitForStableVisibility = (ms) => new Promise(r => setTimeout(r, ms));

        const scrollUntilFooterVisibleStable = async () => {
            while (attempts < maxAttempts) {
                const rect = footer.getBoundingClientRect();
                const isVisible = rect.top >= 0 && rect.bottom <= window.innerHeight;

                if (isVisible) {
                    // Nếu thấy rồi thì chờ 3 giây KHÔNG SCROLL
                    console.log("🟡 Footer visible, waiting 3s...");
                    await waitForStableVisibility(3000);
                    console.log("🟢 Done waiting, checking again...");


                    // Kiểm tra lại sau 3 giây xem còn nằm trong không
                    const rectAfter = footer.getBoundingClientRect();
                    const stillVisible = rectAfter.top >= 0 && rectAfter.bottom <= window.innerHeight;

                    if (stillVisible) {
                        resolve(); // Footer vẫn còn trong viewport sau 3 giây → OK
                        return;
                    }
                    // Nếu rớt ra ngoài sau 3s thì tiếp tục scroll
                }

                window.scrollBy(0, window.innerHeight / 2);
                attempts++;
                await waitForStableVisibility(2000); // đợi 200ms giữa các lần scroll
            }

            resolve(); // Sau quá nhiều lần vẫn không giữ được → dừng
        };

        scrollUntilFooterVisibleStable();
    });
    """

    # JavaScript: Bấm nút "Xem thêm" cho đến khi hết bài viết trong ngày
    click_view_more_until_outdated = """
    new Promise(async resolve => {
        function checkDateTime(lastTimeStr) {
            const [timePart, datePart] = lastTimeStr.split(" ");
            const [hour, minute] = timePart.split(":").map(Number);
            const [day, month, year] = datePart.split("/").map(Number);
            const articleDate = new Date(year, month - 1, day, hour, minute);
            const now = new Date();
            return (
                articleDate.getDate() === now.getDate() &&
                articleDate.getMonth() === now.getMonth() &&
                articleDate.getFullYear() === now.getFullYear()
            );
        }

        async function checkAndClick() {
            let attempts = 0;
            const maxAttempts = 10;

            while (attempts < maxAttempts) {
                const timeSpans = document.querySelectorAll('div.cfbiznews_tt div.time[title]');
                if (timeSpans.length === 0) break;

                const lastTime = timeSpans[timeSpans.length - 1].getAttribute('title');
                if (!checkDateTime(lastTime)) break;

                const viewMore = document.querySelector('div.load-more-cell');
                if (viewMore) {
                    viewMore.click();
                    await new Promise(r => setTimeout(r, 5000));
                } else {
                    break;
                }

                attempts++;
            }

            resolve();
        }

        await checkAndClick();
    });
    """

    # 📦 Schema
    schema_article_top_left = {
        "name": "Article",
        "baseSelector": "div.cfbiz_section-top div.cfbiz_bigleft div.cfbiznews_box div.cfbiznews_total",
        "fields": [
            {"name": "title", "selector": "h2 a", "type": "text"},
            {"name": "href", "selector": "h2 a", "type": "attribute", "attribute": "href"},
            {"name": "description", "selector": "", "type": "text"}
        ]
    }

    schema_article_top_right = {
        "name": "Article",
        "baseSelector": "div.cfbiz_section-top div.cfbiz_bigright-left div.cfbiznews_total",
        "fields": [
            {"name": "title", "selector": "h3 a", "type": "text"},
            {"name": "href", "selector": "h3 a", "type": "attribute", "attribute": "href"},
            {"name": "description", "selector": "", "type": "text"}
        ]
    }

    schema_article_mid = {
        "name": "Article",
        "baseSelector": "div.cfbiz_section-mid div.cfbiz_bigleft div.cfbiznews_total",
        "fields": [
            {"name": "title", "selector": "h3 a", "type": "text"},
            {"name": "href", "selector": "h3 a", "type": "attribute", "attribute": "href"},
            {"name": "description", "selector": "div.sapo", "type": "text"},
            {"name": "time", "selector": "div.cfbiznews_tt div.time.time-ago", "type": "attribute", "attribute": "title"},
        ]
    }

    browser_config = BrowserConfig(
        browser_type="chromium",
        headless=True,
        extra_args=["--disable-extensions"],
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        start = time.time()

        # Step 1: Scroll để hiện nút "Xem thêm"
        await crawler.arun(
            url=link,
            config=CrawlerRunConfig(
                js_code=scroll_to_load_view_more,
                session_id="rimine",
                cache_mode=CacheMode.BYPASS
            )
        )

        # Step 2: Click "Xem thêm" nhiều lần đến khi hết bài hôm nay
        await crawler.arun(
            url=link,
            config=CrawlerRunConfig(
                js_code=click_view_more_until_outdated,
                session_id="rimine",
                js_only=True,
                cache_mode=CacheMode.BYPASS
            )
        )

        # Step 3: Trích xuất dữ liệu
        data = []

        for schema in [schema_article_top_left, schema_article_top_right, schema_article_mid]:
            result = await crawler.arun(
                url=link,
                config=CrawlerRunConfig(
                    session_id="rimine",
                    extraction_strategy=JsonCssExtractionStrategy(schema),
                    js_only=True,
                    cache_mode=CacheMode.BYPASS
                )
            )
            data.extend(json.loads(result.extracted_content))

        end = time.time()
        print(f"✅ Crawl done in {round(end - start, 2)}s")

        # Step 4: Lọc và chuẩn hóa
        articles = []
        for item in data:
            try:
                time_str = item.get("time", "")
                if not check_time(time_str):
                    continue
                articles.append({
                    "title": item.get("title", "").strip(),
                    "href": f"https://cafebiz.vn{item.get('href', '')}",
                    "description": item.get("description", "").strip()
                })
            except Exception as e:
                print(f"[⚠️] Error parsing item: {e}")
                continue

        return articles

        
    

    
    
    
     
     

