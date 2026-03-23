import streamlit as st
import os
import subprocess
import urllib.request
import sys
import pathlib

# 1. إعدادات الصفحة
st.set_page_config(page_title="مُشكِّل النصوص العربية | Rababa", page_icon="📝", layout="centered")

st.markdown("""
    <style>
    body { direction: rtl; text-align: right; font-family: 'Arial', sans-serif;}
    .stTextArea textarea { direction: rtl; text-align: right; font-size: 18px;}
    </style>
""", unsafe_allow_html=True)

# 2. تحديد المسارات الديناميكية
current_dir = pathlib.Path(__file__).parent.resolve()
PYTHON_DIR = current_dir / "python"
DIACRITIZE_SCRIPT = PYTHON_DIR / "diacritize.py"
WEIGHTS_DIR = PYTHON_DIR / "log_dir" / "CA_MSA.base.cbhg" / "models"
WEIGHTS_FILE = WEIGHTS_DIR / "2000000-snapshot.pt"
WEIGHTS_URL = "https://github.com/secryst/rababa-models/releases/download/0.1/2000000-snapshot.pt"

# 3. وظيفة التهيئة
def initialize_assets():
    if not DIACRITIZE_SCRIPT.exists():
        st.error(f"❌ لم يتم العثور على ملف المحرك في: {DIACRITIZE_SCRIPT}")
        return False
    
    if not WEIGHTS_FILE.exists():
        with st.spinner("⏳ جاري تحميل ملفات الذكاء الاصطناعي (50MB)..."):
            try:
                os.makedirs(str(WEIGHTS_DIR), exist_ok=True)
                urllib.request.urlretrieve(WEIGHTS_URL, str(WEIGHTS_FILE))
                st.success("✅ تم تحميل النموذج!")
            except Exception as e:
                st.error(f"❌ فشل التحميل: {e}")
                return False
    return True

# 4. الواجهة
st.title("📝 مُشكِّل النصوص العربية الذكي")
assets_ready = initialize_assets()
user_text = st.text_area("أدخل النص العربي:", height=150)

if st.button("تـشـكـيـل الـنـص 🚀", type="primary", use_container_width=True):
    if assets_ready and user_text.strip():
        with st.spinner("⏳ جاري المعالجة..."):
            command = [
                sys.executable, "diacritize.py", 
                "--model_kind", "cbhg", 
                "--config", "config/cbhg.yml", 
                "--text", user_text
            ]
            try:
                result = subprocess.run(command, cwd=str(PYTHON_DIR), capture_output=True, text=True, encoding="utf-8")
                if result.returncode == 0:
                    lines = [l.strip() for l in result.stdout.split('\n') if l.strip()]
                    st.text_area("النتيجة:", value=lines[-1] if lines else "", height=150)
                else:
                    st.error(f"❌ خطأ: {result.stderr}")
            except Exception as e:
                st.error(f"❌ خطأ نظام: {e}")
