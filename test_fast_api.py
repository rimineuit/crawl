from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
import json
import sys
import os

app = FastAPI()
env = os.environ.copy()

env["PYTHONIOENCODING"] = "utf-8"
env["PYTHONUTF8"] = "1"
class URLInput(BaseModel):
    url: str
    source: str

import sys
@app.get("/check")
def check_env():
    return {"python_executable": sys.executable}
    
    
@app.get("/crawl/fireant")
def crawl_links():
    try:
        path = "crawl/run_crawl/fireant.py"
        script_path = os.path.abspath(path)
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            check=True,
            env=env,
            encoding='utf-8'
        )
        matches = re.findall(r"\[\{.*\]", result.stdout, re.DOTALL)
        json_str = matches[-1] if matches else None
        if not json_str:
            return {
                "error": "Không tìm thấy JSON trong stdout",
                "stdout": result.stdout
            }

        return json.loads(json_str)
    except subprocess.CalledProcessError as e:
        return {"error": "Script lỗi", "details": e.stderr}
    
@app.get("/crawl/vietstock")
def crawl_links_vietstock():

    try:
        path = "crawl/run_crawl/vietstock.py"
        script_path = os.path.abspath(path)
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            check=True,
            env=env,
            encoding='utf-8'
        )
        matches = re.findall(r"\[\{.*\]", result.stdout, re.DOTALL)
        json_str = matches[-1] if matches else None
        if not json_str:
            return {
                "error": "Không tìm thấy JSON trong stdout",
                "stdout": result.stdout
            }

        return json.loads(json_str)
    except subprocess.CalledProcessError as e:
        return {"error": "Script lỗi", "details": e.stderr}

import re

@app.get("/embedding_articles")
def embedding_articles():
    try:
        path = "embedding_vector.py"
        script_path = os.path.abspath(path)
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            check=True,
            env=env,
            encoding='utf-8'
        )
        return {"Success"}
    except:
        return {"error"}
class Query(BaseModel):
    query: str
    
    
@app.post("/embedding_query")
def embedding_query(input_data: Query):
    try:
        path = "embedding_query.py"
        script_path = os.path.abspath(path)
        result = subprocess.run(
            [sys.executable, script_path, input_data.query],
            capture_output=True,
            text=True,
            check=True,
            env=env,
            encoding='utf-8'
        )
        if not result:
            return {
                "error": "Không tìm thấy embedding trong stdout",
            }
        return json.loads(result.stdout)
    except:
        return {"error": "Không thể embedding query"}
    

@app.post("/scrape")
def scrape_articles(input_data: URLInput):
    try:
        script_path = os.path.abspath("scrape_articles_by_source.py")
        result = subprocess.run(
            [sys.executable, script_path, input_data.url, input_data.source],
            capture_output=True,
            text=True,
            check=True,
            env=env,
            encoding='utf-8'
        )

        # 🧠 Lọc phần JSON cuối cùng từ stdout
        matches = re.findall(r"\{.*\}", result.stdout, re.DOTALL)
        json_str = matches[-1] if matches else None

        if not json_str:
            return {
                "error": "Không tìm thấy JSON trong stdout",
                "stdout": result.stdout
            }

        return json.loads(json_str)

    except subprocess.CalledProcessError as e:
        return {"error": "Script lỗi", "details": e.stderr}
    except json.JSONDecodeError as e:
        return {
            "error": "JSON decode error",
            "stdout": result.stdout,
            "details": str(e)
        }
class VideoBody(BaseModel):
    url: str                  # YouTube (hoặc link yt-dlp hỗ trợ)

@app.post("/youtube/upload")
async def youtube_upload(body: VideoBody):
    """
    Gọi script video2gemini_upload.py -> trả JSON upload của Gemini.
    """
    try:
        path = "video2gemini_uploads.py"
        script_path = os.path.abspath(path)
        proc = subprocess.run(
            [sys.executable, script_path, body.url.strip().rstrip(";")],
            timeout=900,
            capture_output=True,
            text=True,
            check=True,
            env=env,
            encoding='utf-8'# 15′; đủ cho video vài trăm MB
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Quá thời gian xử lý")

    if proc.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail=f"yt-dlp/Gemini error:\n{proc.stderr}"
        )

    # Tìm đoạn JSON trong stdout bằng regex
    try:
        json_text_match = re.search(r"{[\s\S]+}", proc.stdout)
        if not json_text_match:
            raise ValueError("Không tìm thấy đoạn JSON hợp lệ trong stdout")
        json_text = json_text_match.group(0)
        result_json = json.loads(json_text)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Không parse được JSON từ script: {e}\nSTDOUT:\n{proc.stdout}"
        )
    return result_json