import streamlit as st
import os
import subprocess

# 1. إعدادات الصفحة
st.set_page_config(page_title="مُشكِّل النصوص | Rababa", page_icon="📝", layout="centered")

# 2. تصميم الواجهة (دعم اللغة العربية)
st.markdown("""
    <style>
    body { direction: rtl; text-align: right; font-family: 'Arial', sans-serif;}
    .stTextArea textarea { direction: rtl; text-align: right; font-size: 18px;}
    </style>
""", unsafe_allow_html=True)

st.title("📝 التشكيل الآلي للنصوص العربية")
st.markdown("هذه الواجهة تعتمد على نموذج **Rababa (CBHG)** للذكاء الاصطناعي.")
st.markdown("---")

user_text = st.text_area("أدخل النص غير المُشكل هنا:", height=150, placeholder="مثال: اللغة العربية بحر عميق...")

if st.button("تـشـكـيـل الـنـص 🚀", type="primary", use_container_width=True):
    if not user_text.strip():
        st.warning("⚠️ الرجاء إدخال نص أولاً!")
    else:
        with st.spinner("⏳ جاري تحليل الجملة ووضع الحركات..."):
            
            # --- التعديل هنا ليتناسب مع موقع app.py الجديد ---
            # يبحث عن مجلد python الموجود بجوار ملف app.py مباشرة
            python_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "python"))
            
            if not os.path.exists(python_dir):
                st.error("❌ لم يتم العثور على مجلد 'python'. تأكد من هيكلة الملفات.")
            else:
                # تجهيز أمر التشغيل
                command = [
                    "python", "diacritize.py", 
                    "--model_kind", "cbhg", 
                    "--config", "config/cbhg.yml", 
                    "--text", user_text
                ]
                
                try:
                    # تشغيل الأداة في الخلفية (نطلب منه العمل من داخل مجلد python)
                    result = subprocess.run(command, cwd=python_dir, capture_output=True, text=True, encoding="utf-8")
                    
                    if result.returncode != 0:
                        st.error(f"❌ حدث خطأ في النموذج:\n{result.stderr.strip()}")
                    else:
                        lines = [line.strip() for line in result.stdout.split('\n') if line.strip()]
                        if lines:
                            diacritized_text = lines[-1]
                            st.success("✅ تم التشكيل بنجاح!")
                            st.text_area("النص المُشكل:", value=diacritized_text, height=150)
                        else:
                            st.warning("⚠️ النموذج لم يرجع أي نتيجة.")
                            
                except Exception as e:
                    st.error(f"❌ خطأ في النظام: {e}")

st.markdown("---")
st.caption("تم التطوير باستخدام Streamlit و نموذج Rababa.")
