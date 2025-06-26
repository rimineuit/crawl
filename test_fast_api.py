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
    try:
        script_path = os.path.abspath("video2gemini_uploads.py")
        url = body.url.strip()
        print(url)
        url = re.sub(r"[;]+$", "", body.url.strip())
        print("after:", url)
        print("🔧 subprocess args:", [sys.executable, script_path, url])
        print("🌐 sys.executable:", sys.executable)
        print("📂 script_path:", script_path)
        print("🌍 ENV LANG:", os.environ.get("LANG"))
        print("🌍 ENV LC_ALL:", os.environ.get("LC_ALL"))

        proc = subprocess.run(
            [sys.executable, script_path, url],
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8',
            env=env
        )

    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500,
            detail=f"""❌ Subprocess error:
            STDOUT:
            {e.stdout}
            STDERR:
            {e.stderr}
            ARGS:
            {e.cmd}
            """
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="⏰ Quá thời gian xử lý subprocess")

    # Tìm JSON trong stdout
    try:
        json_text_match = re.search(r"{[\s\S]+}", proc.stdout)
        if not json_text_match:
            raise ValueError("Không tìm thấy JSON trong stdout")
        result_json = json.loads(json_text_match.group(0))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Không parse được JSON từ script: {e}\nSTDOUT:\n{proc.stdout}"
        )

    return result_json