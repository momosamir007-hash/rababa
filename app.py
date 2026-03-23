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

# 2. تحديد المسارات الذكية (Smart Paths)
# الحصول على المسار الأساسي للمشروع على السيرفر
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# المسار المتوقع لمجلد python (تأكد أن اسمه python بحروف صغيرة في GitHub)
PYTHON_DIR = os.path.join(BASE_DIR, "python")
DIACRITIZE_SCRIPT = os.path.join(PYTHON_DIR, "diacritize.py")
CONFIG_FILE = os.path.join(PYTHON_DIR, "config", "cbhg.yml")

# مسار ملف الأوزان (Weights)
WEIGHTS_DIR = os.path.join(PYTHON_DIR, "log_dir", "CA_MSA.base.cbhg", "models")
WEIGHTS_FILE = os.path.join(WEIGHTS_DIR, "2000000-snapshot.pt")
WEIGHTS_URL = "https://github.com/secryst/rababa-models/releases/download/0.1/2000000-snapshot.pt"

# 3. وظيفة التحميل التلقائي للأوزان
def initialize_assets():
    if not os.path.exists(PYTHON_DIR):
        st.error(f"❌ لم يتم العثور على مجلد 'python'. المسار الحالي: {BASE_DIR}")
        return False
    
    if not os.path.exists(WEIGHTS_FILE):
        with st.spinner("⏳ جاري تحميل ملفات الذكاء الاصطناعي لأول مرة (50MB)..."):
            try:
                os.makedirs(WEIGHTS_DIR, exist_ok=True)
                urllib.request.urlretrieve(WEIGHTS_URL, WEIGHTS_FILE)
                st.success("✅ تم تحميل النموذج بنجاح!")
            except Exception as e:
                st.error(f"❌ فشل تحميل الأوزان: {e}")
                return False
    return True

# 4. واجهة المستخدم الرئيسية
st.title("📝 مُشكِّل النصوص العربية الذكي")
st.markdown("تطبيق ويب يعتمد على نموذج **Rababa** لتشكيل النصوص العربية بدقة عالية.")
st.markdown("---")

# التأكد من جاهزية الملفات قبل السماح للمستخدم بالكتابة
assets_ready = initialize_assets()

user_text = st.text_area("أدخل النص العربي المراد تشكيله:", height=150, placeholder="مثال: ان المشروع يهدف الى تطوير ادوات الذكاء الاصطناعي...")

if st.button("تـشـكـيـل الـنـص 🚀", type="primary", use_container_width=True):
    if not assets_ready:
        st.error("❌ لا يمكن التشغيل بسبب فقدان ملفات النظام.")
    elif not user_text.strip():
        st.warning("⚠️ يرجى إدخال نص أولاً.")
    else:
        with st.spinner("⏳ جاري تحليل النص..."):
            # تجهيز أمر التشغيل باستخدام python الخاص بالبيئة الحالية (sys.executable)
            command = [
                sys.executable, 
                "diacritize.py", 
                "--model_kind", "cbhg", 
                "--config", "config/cbhg.yml", 
                "--text", user_text
            ]
            
            try:
                # تنفيذ العملية من داخل مجلد python لضمان عمل المسارات النسبية داخل المشروع
                result = subprocess.run(
                    command, 
                    cwd=PYTHON_DIR, 
                    capture_output=True, 
                    text=True, 
                    encoding="utf-8"
                )
                
                if result.returncode != 0:
                    st.error(f"❌ خطأ داخلي في المحرك:\n{result.stderr.strip()}")
                else:
                    # سحب النص المشكل (آخر سطر غير فارغ في المخرجات)
                    lines = [line.strip() for line in result.stdout.split('\n') if line.strip()]
                    if lines:
                        diacritized_result = lines[-1]
                        st.success("✅ تم التشكيل!")
                        st.text_area("النتيجة:", value=diacritized_result, height=150)
                    else:
                        st.warning("⚠️ لم يتم استرجاع أي نتائج من النموذج.")
                        
            except Exception as e:
                st.error(f"❌ حدث خطأ غير متوقع: {e}")

st.markdown("---")
st.caption("التطبيق يعمل بواسطة Rababa و Streamlit Cloud.")
