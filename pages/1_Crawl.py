import streamlit as st
import subprocess
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
st.title("🕷️ Crawl dữ liệu từ nguồn")

sources = {
    "FireAnt": "python crawl/run_crawl/fireant.py",
    "Cafef": "python crawl/run_crawl/cafef.py",
    "Cafebiz": "python crawl/run_crawl/cafebiz.py",
    "Vietstock": "python crawl/run_crawl/vietstock.py"
}

selected_sources = st.multiselect("Chọn nguồn cần crawl:", list(sources.keys()))

if st.button("Bắt đầu Crawl"):
    for src in selected_sources:
        st.write(f"🚀 Đang crawl {src}...")
        command = sources[src].split()
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
        if result.returncode == 0:
            st.success(f"✅ Crawl {src} thành công")
            st.code(result.stdout)
        else:
            st.error(f"❌ Lỗi khi crawl {src}")
            st.code(result.stderr)
