import streamlit as st
import os
import subprocess
import urllib.request

# 1. إعدادات الصفحة والتصميم
st.set_page_config(page_title="مُشكِّل النصوص العربية | Rababa", page_icon="📝", layout="centered")

st.markdown("""
    <style>
    body { direction: rtl; text-align: right; font-family: 'Arial', sans-serif;}
    .stTextArea textarea { direction: rtl; text-align: right; font-size: 18px;}
    </style>
""", unsafe_allow_html=True)

# 2. وظيفة التحميل التلقائي للأوزان (Weights)
def download_weights():
    # المسار المطلوب لملف الأوزان داخل مجلد python
    target_dir = os.path.join(os.path.dirname(__file__), "python", "log_dir", "CA_MSA.base.cbhg", "models")
    target_file = os.path.join(target_dir, "2000000-snapshot.pt")
    
    # رابط التحميل المباشر للأوزان
    weights_url = "https://github.com/secryst/rababa-models/releases/download/0.1/2000000-snapshot.pt"
    
    if not os.path.exists(target_file):
        with st.spinner("⏳ جاري تحميل ملفات الذكاء الاصطناعي لأول مرة (حوالي 50 ميجابايت)..."):
            os.makedirs(target_dir, exist_ok=True)
            urllib.request.urlretrieve(weights_url, target_file)
            st.success("✅ تم تحميل ملفات النموذج بنجاح!")

# تشغيل وظيفة التحميل عند بدء التطبيق
download_weights()

# 3. واجهة المستخدم
st.title("📝 مُشكِّل النصوص العربية الذكي")
st.markdown("هذا التطبيق يستخدم نموذج **Rababa** القائم على أبحاث التعلم العميق لتشكيل النصوص بدقة.")
st.markdown("---")

user_text = st.text_area("أدخل النص العربي (بدون تشكيل):", height=150, placeholder="مثال: ذهب الطالب الى المدرسة...")

if st.button("تـشـكـيـل الـنـص 🚀", type="primary", use_container_width=True):
    if not user_text.strip():
        st.warning("⚠️ يرجى كتابة نص للتشكيل.")
    else:
        with st.spinner("⏳ جاري المعالجة..."):
            # تحديد مسار مجلد بايثون
            python_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "python"))
            
            # أمر التشغيل
            command = [
                "python", "diacritize.py", 
                "--model_kind", "cbhg", 
                "--config", "config/cbhg.yml", 
                "--text", user_text
            ]
            
            try:
                # تنفيذ عملية التشكيل
                result = subprocess.run(command, cwd=python_dir, capture_output=True, text=True, encoding="utf-8")
                
                if result.returncode != 0:
                    st.error(f"❌ خطأ في المحرك الداخلي:\n{result.stderr.strip()}")
                else:
                    lines = [line.strip() for line in result.stdout.split('\n') if line.strip()]
                    if lines:
                        diacritized_text = lines[-1]
                        st.success("✅ تمت العملية!")
                        st.text_area("النص بعد التشكيل:", value=diacritized_text, height=150)
                    else:
                        st.error("⚠️ فشل النموذج في توليد مخرجات.")
            except Exception as e:
                st.error(f"❌ حدث خطأ غير متوقع: {e}")

st.markdown("---")
st.caption("تم التطوير باستخدام Rababa و Streamlit.")
