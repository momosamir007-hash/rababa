import streamlit as st
import os
import subprocess
import urllib.request
import sys
from pathlib import Path

# 1. إعدادات الصفحة
st.set_page_config(page_title="مُشكِّل النصوص العربية", page_icon="📝")

# 2. وظيفة البحث الديناميكي عن المجلد (Smart Finder)
def find_python_dir():
    # البحث عن ملف diacritize.py في المجلد الحالي وكل المجلدات الفرعية
    for path in Path(os.getcwd()).rglob('diacritize.py'):
        # إذا وجده، يرجع المسار الأب له (مجلد python)
        return path.parent.absolute()
    return None

PYTHON_DIR = find_python_dir()

# 3. واجهة المستخدم والتصميم
st.markdown("<style>body { direction: rtl; text-align: right; }</style>", unsafe_allow_html=True)
st.title("📝 مُشكِّل النصوص العربية الذكي")

if PYTHON_DIR is None:
    st.error("❌ لم يتم العثور على ملف المحرك diacritize.py في أي مكان داخل المستودع!")
    st.info(f"المسار الحالي الذي يبحث فيه السيرفر هو: {os.getcwd()}")
    st.stop()

# تعريف المسارات بناءً على ما وجده البحث
DIACRITIZE_SCRIPT = os.path.join(PYTHON_DIR, "diacritize.py")
WEIGHTS_DIR = os.path.join(PYTHON_DIR, "log_dir", "CA_MSA.base.cbhg", "models")
WEIGHTS_FILE = os.path.join(WEIGHTS_DIR, "2000000-snapshot.pt")
WEIGHTS_URL = "https://github.com/secryst/rababa-models/releases/download/0.1/2000000-snapshot.pt"

# 4. تحميل الأوزان إذا نقصت
if not os.path.exists(WEIGHTS_FILE):
    with st.spinner("⏳ جاري تحميل ملفات الذكاء الاصطناعي (أول مرة فقط)..."):
        os.makedirs(WEIGHTS_DIR, exist_ok=True)
        urllib.request.urlretrieve(WEIGHTS_URL, WEIGHTS_FILE)

# 5. منطق التشغيل
user_text = st.text_area("أدخل النص العربي:", height=150)

if st.button("تـشـكـيـل الـنـص 🚀", type="primary", use_container_width=True):
    if user_text.strip():
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
                    st.success("✅ تمت العملية!")
                    st.text_area("النتيجة:", value=lines[-1] if lines else "", height=150)
                else:
                    st.error(f"❌ خطأ من المحرك: {result.stderr}")
            except Exception as e:
                st.error(f"❌ خطأ نظام: {e}")
