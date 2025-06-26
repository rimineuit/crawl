# from youtube_transcript_api import YouTubeTranscriptApi

# ytt_api = YouTubeTranscriptApi()
# fetched_transcript =  ytt_api.fetch("th6ivLDEz2Q",languages=['vi', 'en'])
# transcript_list = ytt_api.list('th6ivLDEz2Q')
# print(transcript_list)
# # is iterable
# for snippet in fetched_transcript:
#     print(snippet.text)

# # indexable
# last_snippet = fetched_transcript[-1]

# # provides a length
# snippet_count = len(fetched_transcript)


import requests

api_key = 'AIzaSyBUwBMbdeD_l6rQ_TJiLuA3eilOrdbm6AQ'
upload_url = f"https://generativelanguage.googleapis.com/upload/v1beta/files?key={api_key}"

with open("video.mp4", "rb") as f:
    response = requests.post(upload_url, files={"file": ("video.mp4", f, "video/mp4")})
    print(response.json())
