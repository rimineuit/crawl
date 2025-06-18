from fastapi import FastAPI, Request
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
    
    
@app.get("/crawl")
def crawl_links():
    try:
        paths = ["crawl/run_crawl/fireant.py","crawl/run_crawl/vietstock.py"]
        for path in paths:
            script_path = os.path.abspath(path)
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                check=True,
                env=env,
                encoding='utf-8'
            )
            print(">>> STDOUT:", result.stdout)
            
        return {"message": "done"}  # ✅ thêm dòng này
    except subprocess.CalledProcessError as e:
        return {"error": "Script lỗi", "details": e.stderr}
        
import re


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
