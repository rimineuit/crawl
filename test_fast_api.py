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

import sys
@app.get("/check")
def check_env():
    return {"python_executable": sys.executable}

@app.post("/scrape")
def scrape_article(input_data: URLInput):
    try:
        script_path = os.path.abspath("t.py")
        result = subprocess.run(
            [sys.executable, script_path, input_data.url],
            capture_output=True,
            text=True,
            check=True,
            env=env,
            encoding='utf-8'
        )
        print(">>> STDOUT:", result.stdout)
        return json.loads(result.stdout)  # Script phải in ra JSON hợp lệ
    except subprocess.CalledProcessError as e:
        return {"error": "Script lỗi", "details": e.stderr}
    except json.JSONDecodeError as e:
        return {"error": "JSON decode error", "stdout": result.stdout, "details": str(e)}
    
    
@app.get("/crawl")
def crawl_links():
    try:
        paths = ["crawl/run_crawl/fireant.py","crawl/run_crawl/vietstock.py"]
        for path in paths:
            script_path = os.path.abspath(path)
            subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                check=True,
                env=env,
                encoding='utf-8'
            )
    except subprocess.CalledProcessError as e:
        return {"error": "Script lỗi", "details": e.stderr}
        
        
