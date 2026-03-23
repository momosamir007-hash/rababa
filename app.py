import streamlit as st
import os
import subprocess
import urllib.request
import sys

# 1. إعدادات الصفحة والتصميم
st.set_page_config(page_title="مُشكِّل النصوص العربية | Rababa", page_icon="📝", layout="centered")

st.markdown("""
    <style>
    body { direction: rtl; text-align: right; font-family: 'Arial', sans-serif;}
    .stTextArea textarea { direction: rtl; text-align: right; font-size: 18px;}
    .stAlert { direction: rtl; text-align: right;}
    </style>
""", unsafe_allow_html=True)

# --- 2. تحديد المسارات بطريقة ديناميكية ذكية ---
# هذا السطر سيجلب المسار الحالي للمجلد الذي يعمل فيه app.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# البحث عن مجلد python:
# أولاً: نجرب إذا كان المجلد موجوداً مباشرة بجانب app.py (كما في صورتك الأخيرة)
PYTHON_DIR = os.path.join(BASE_DIR, "python")

# ثانياً: إذا لم يجده، نجرب البحث داخل مجلد فرعي اسمه rababa (للاحتياط)
if not os.path.exists(PYTHON_DIR):
    PYTHON_DIR = os.path.join(BASE_DIR, "rababa", "python")

DIACRITIZE_SCRIPT = os.path.join(PYTHON_DIR, "diacritize.py")
WEIGHTS_DIR = os.path.join(PYTHON_DIR, "log_dir", "CA_MSA.base.cbhg", "models")
WEIGHTS_FILE = os.path.join(WEIGHTS_DIR, "2000000-snapshot.pt")
WEIGHTS_URL = "https://github.com/secryst/rababa-models/releases/download/0.1/2000000-snapshot.pt"

# --- 3. وظيفة التحميل التلقائي للأوزان ---
def initialize_assets():
    if not os.path.exists(DIACRITIZE_SCRIPT):
        st.error(f"❌ لم يتم العثور على ملف المحرك diacritize.py في المسار: {DIACRITIZE_SCRIPT}")
        st.info("تأكد أن مجلد 'python' موجود في GitHub بنفس مستوى ملف app.py وبحروف صغيرة.")
        return False
    
    if not os.path.exists(WEIGHTS_FILE):
        with st.spinner("⏳ جاري تحميل ملفات الذكاء الاصطناعي (50MB)..."):
            try:
                os.makedirs(WEIGHTS_DIR, exist_ok=True)
                urllib.request.urlretrieve(WEIGHTS_URL, WEIGHTS_FILE)
                st.success("✅ تم تحميل النموذج بنجاح!")
            except Exception as e:
                st.error(f"❌ فشل تحميل الأوزان: {e}")
                return False
    return True

# --- 4. واجهة المستخدم ---
st.title("📝 مُشكِّل النصوص العربية الذكي")
st.markdown("---")

assets_ready = initialize_assets()

user_text = st.text_area("أدخل النص العربي المراد تشكيله:", height=150)

if st.button("تـشـكـيـل الـنـص 🚀", type="primary", use_container_width=True):
    if not assets_ready:
        st.error("❌ النظام غير جاهز للعمل.")
    elif not user_text.strip():
        st.warning("⚠️ يرجى إدخال نص.")
    else:
        with st.spinner("⏳ جاري المعالجة..."):
            # استخدام sys.executable لضمان استخدام بايثون الخاص بالسيرفر
            command = [
                sys.executable, 
                "diacritize.py", 
                "--model_kind", "cbhg", 
                "--config", "config/cbhg.yml", 
                "--text", user_text
            ]
            
            try:
                result = subprocess.run(
                    command, 
                    cwd=PYTHON_DIR, 
                    capture_output=True, 
                    text=True, 
                    encoding="utf-8"
                )
                
                if result.returncode != 0:
                    st.error(f"❌ خطأ داخلي:\n{result.stderr.strip()}")
                else:
                    lines = [line.strip() for line in result.stdout.split('\n') if line.strip()]
                    if lines:
                        st.success("✅ تم!")
                        st.text_area("النتيجة:", value=lines[-1], height=150)
            except Exception as e:
                st.error(f"❌ خطأ غير متوقع: {e}")
