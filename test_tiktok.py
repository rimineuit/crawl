from TikTokApi import TikTokApi
import asyncio
import os

ms_token = os.environ.get("5cUOQtvTc9cHFl_YG6Pqgv7jB8N33y1Mq2Gh2Bz-lBWAJfScYloJ21Yw-cyGzex4p4pKGtES-0vHKwJY-v9l_hc8WjIKJ1OQlQbFnH2p4-EDPCXa1G6lmF0q5owK-JMfKA2qTsGmtrWCOw==", None) # get your own ms_token from your cookies on tiktok.com

async def trending_videos():
    async with TikTokApi() as api:
        await api.create_sessions(ms_tokens=[ms_token], num_sessions=1, sleep_after=3, browser=os.getenv("TIKTOK_BROWSER", "chromium"))
        async for video in api.trending.videos(count=30):
            print(video)
            print(video.as_dict)

if __name__ == "__main__":
    asyncio.run(trending_videos())