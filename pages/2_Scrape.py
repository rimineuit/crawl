import streamlit as st
import tempfile
import subprocess
import json
import os
from collections import defaultdict

st.title("🔍 Lọc bài viết theo từ khóa từ DB")

# --- Nhập từ khóa ---
input_method = st.radio("Chọn cách nhập từ khóa:", ["Gõ từ khóa", "Tải file .txt"])
keywords = []

if input_method == "Gõ từ khóa":
    query = st.text_area("🔑 Nhập từ khóa, cách nhau bởi dấu phẩy hoặc xuống dòng", height=150)
    if query:
        keywords = [kw.strip() for kw in query.replace(",", "\n").splitlines() if kw.strip()]
elif input_method == "Tải file .txt":
    uploaded_file = st.file_uploader("📄 Upload file .txt (mỗi dòng 1 từ khóa)", type="txt")
    if uploaded_file is not None:
        content = uploaded_file.read().decode("utf-8")
        keywords = [kw.strip() for kw in content.splitlines() if kw.strip()]

# --- Số lượng kết quả ---
limit = st.slider("📄 Giới hạn số bài viết hiển thị", 5, 100, 20)

# --- Chạy lọc bằng subprocess ---
if st.button("🚀 Bắt đầu lọc và scrape lại"):
    if not keywords:
        st.warning("❗ Bạn cần nhập ít nhất 1 từ khóa.")
    else:
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".txt", encoding="utf-8") as tmp:
            for kw in keywords:
                tmp.write(kw + "\n")
            tmp_path = tmp.name

        process = subprocess.run(
            ["python", "run_filter.py", tmp_path],
            capture_output=True,
            text=True,
            encoding="utf-8"
        )

        if process.returncode == 0:
            try:
                articles = json.loads(process.stdout)
                st.session_state["matched_articles"] = articles[:limit]
                st.success(f"✅ Tìm thấy {len(articles[:limit])} bài viết khớp.")
            except json.JSONDecodeError:
                st.error("❌ Không đọc được dữ liệu từ subprocess.")
        else:
            st.error("❌ Lỗi khi chạy subprocess.")
            st.code(process.stderr)

# --- Chọn bài viết để giữ ---
if "matched_articles" in st.session_state:
    matched_articles = st.session_state["matched_articles"]
    grouped_selected = defaultdict(list)

    st.subheader("📝 Chọn bài viết muốn giữ lại")
    for i, item in enumerate(matched_articles):
        if st.checkbox(f"{item['title']}", key=f"article_{i}", value=True):
            source = item.get("source", "unknown").lower()
            grouped_selected[source].append(item)

        st.markdown(f"[🔗 Xem bài viết]({item['href']})", unsafe_allow_html=True)
        st.write(item['description'])
        st.markdown("---")

    # --- Lưu thành file tạm và chạy subprocess ---
    if st.button("💾 Lưu và chạy theo từng source"):
        script_mapping = {
            "fireant": "python scrape/run_scrape/fireant.py",
            "cafef": "python scrape/run_scrape/cafef.py",
            "vietstock": "python scrape/run_scrape/vietstock.py",
            "cafebiz": "python scrape/run_scrape/cafebiz.py",
        }

        for source, articles in grouped_selected.items():
            with tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".json", encoding="utf-8") as tf:
                json.dump(articles, tf, ensure_ascii=False, indent=2)
                temp_json_path = tf.name

            st.success(f"✅ Đã lưu {len(articles)} bài của `{source}` vào file tạm `{temp_json_path}`")

            source_key = source.lower()
            script_cmd = script_mapping.get(source_key)

            if script_cmd:
                result = subprocess.run(
                    script_cmd.split() + [temp_json_path],
                    capture_output=True,
                    text=True,
                    encoding="utf-8"
                )

                if result.returncode == 0:
                    st.success(f"🚀 Script {source} chạy thành công")
                    st.code(result.stdout)
                else:
                    st.error(f"❌ Script {source} bị lỗi")
                    st.code(result.stderr)
            else:
                st.warning(f"⚠️ Không có script cho nguồn `{source}`")
