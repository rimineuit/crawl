from fastapi import FastAPI, HTTPException, Request
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
    url: str
    
    
@app.middleware("http")
async def log_request(request: Request, call_next):
    body = await request.body()
    print("📥 RAW request body:", body.decode("utf-8", errors="replace"))
    response = await call_next(request)
    return response

@app.post("/youtube/upload")
async def youtube_upload(body: VideoBody):
    # Làm sạch URL khỏi dấu ; nếu có
    clean_url = body.url.strip().rstrip(';')

    print("📥 URL nhận được (raw):", body.url)
    print("📥 URL sau khi làm sạch:", repr(clean_url))

    # Đường dẫn tuyệt đối tới script (nếu cần)
    script_path = "video2gemini_uploads.py"  # hoặc /app/video2gemini_uploads.py nếu dùng Railway

    cmd = ["python3", script_path, clean_url]
    print("🔧 subprocess args:", cmd)

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=900,
            env=env
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="⏱️ Quá thời gian xử lý")

    if proc.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail=f"yt-dlp/Gemini error:\n{proc.stderr}"
        )

    # Tìm đoạn JSON trong stdout
    import re
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