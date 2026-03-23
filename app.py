import streamlit as st
import os
import subprocess

# 1. إعدادات الصفحة (يجب أن تكون أول سطر)
st.set_page_config(page_title="مُشكِّل النصوص | Rababa", page_icon="📝", layout="centered")

# 2. تصميم الواجهة (دعم اللغة العربية والاتجاه من اليمين لليسار)
st.markdown("""
    <style>
    body { direction: rtl; text-align: right; font-family: 'Arial', sans-serif;}
    .stTextArea textarea { direction: rtl; text-align: right; font-size: 18px;}
    </style>
""", unsafe_allow_html=True)

st.title("📝 التشكيل الآلي للنصوص العربية")
st.markdown("هذه الواجهة تعتمد على نموذج **Rababa (CBHG)** للذكاء الاصطناعي.")
st.markdown("---")

# 3. مربع إدخال النص
user_text = st.text_area("أدخل النص غير المُشكل هنا:", height=150, placeholder="مثال: اللغة العربية بحر عميق...")

# 4. زر التشغيل والمنطق البرمجي
if st.button("تـشـكـيـل الـنـص 🚀", type="primary", use_container_width=True):
    if not user_text.strip():
        st.warning("⚠️ الرجاء إدخال نص أولاً!")
    else:
        with st.spinner("⏳ جاري تحليل الجملة ووضع الحركات..."):
            
            # تحديد مسار مجلد بايثون داخل مستودع ربابة
            # نفترض أن ملف app.py موجود بجوار مجلد rababa
            rababa_dir = os.path.abspath(os.path.join(os.getcwd(), "rababa", "python"))
            
            if not os.path.exists(rababa_dir):
                st.error("❌ لم يتم العثور على مجلد 'rababa/python'. تأكد من تحميل المستودع بجوار ملف app.py.")
            else:
                # تجهيز أمر سطر الأوامر لتشغيل النموذج
                command = [
                    "python", "diacritize.py", 
                    "--model_kind", "cbhg", 
                    "--config", "config/cbhg.yml", 
                    "--text", user_text
                ]
                
                try:
                    # تشغيل الأداة في الخلفية والتقاط النتيجة
                    # cwd=rababa_dir تجعل الكود يعمل وكأنه داخل مجلد ربابة
                    result = subprocess.run(command, cwd=rababa_dir, capture_output=True, text=True, encoding="utf-8")
                    
                    if result.returncode != 0:
                        st.error(f"❌ حدث خطأ في النموذج:\n{result.stderr.strip()}")
                    else:
                        # سحب النص المُشكل من السطر الأخير
                        lines = [line.strip() for line in result.stdout.split('\n') if line.strip()]
                        if lines:
                            diacritized_text = lines[-1]
                            st.success("✅ تم التشكيل بنجاح!")
                            # عرض النتيجة في مربع نصوص جديد
                            st.text_area("النص المُشكل:", value=diacritized_text, height=150)
                        else:
                            st.warning("⚠️ النموذج لم يرجع أي نتيجة.")
                            
                except Exception as e:
                    st.error(f"❌ خطأ في النظام: {e}")

st.markdown("---")
st.caption("تم التطوير باستخدام Streamlit و نموذج Rababa.")
