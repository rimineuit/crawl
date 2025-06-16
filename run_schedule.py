import subprocess

scripts = [
    "crawl/run_crawl/vietstock.py",
    "crawl/run_crawl/cafef.py",
    "crawl/run_crawl/cafebiz.py",
    "crawl/run_crawl/fireant.py",
    "embedding_vector.py"
]

for script in scripts:
    print(f"⏳ Đang chạy: {script}")
    subprocess.run(["python", script])
    print(f"✅ Xong: {script}\n")
