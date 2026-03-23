import streamlit as st
import os
import subprocess
import urllib.request
import sys
from pathlib import Path

# =============================================
# 1. إعدادات الصفحة
# =============================================
st.set_page_config(page_title="مُشكِّل النصوص العربية", page_icon="📝")

# =============================================
# 2. تثبيت المكتبات الناقصة تلقائياً
# =============================================
def install_missing_packages():
    """تثبيت أي مكتبة ناقصة يحتاجها محرك التشكيل"""
    required_packages = [
        "tqdm",
        "torch",
        "numpy",
        "pyyaml",
        "onnxruntime"
    ]
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            st.toast(f"⏳ جاري تثبيت {package}...")
            subprocess.check_call([
                sys.executable,
                "-m",
                "pip",
                "install",
                package,
                "-q"
            ])

# تشغيل التثبيت عند أول تحميل فقط
if "packages_installed" not in st.session_state:
    with st.spinner("⏳ جاري تجهيز البيئة (أول مرة فقط)..."):
        install_missing_packages()
    st.session_state.packages_installed = True

# =============================================
# 3. وظيفة البحث الذكي عن المجلد الصحيح (العربي)
# =============================================
def find_arabic_python_dir():
    """ البحث عن diacritize.py في المجلد العربي تحديداً وليس العبري أو أي مجلد آخر """
    cwd = Path(os.getcwd())

    # === الأولوية 1: البحث عن المسار العربي تحديداً ===
    arabic_patterns = [
        "python/diacritize.py",        # مباشرة
        "python/arabic/diacritize.py", # داخل مجلد arabic
        "arabic/diacritize.py",        # مجلد arabic مباشر
    ]
    for pattern in arabic_patterns:
        candidate = cwd / pattern
        if candidate.exists():
            return candidate.parent.absolute()

    # === الأولوية 2: البحث العام مع استبعاد hebrew ===
    all_matches = list(cwd.rglob("diacritize.py"))
    for match in all_matches:
        # استبعاد مجلد hebrew
        if "hebrew" not in str(match).lower():
            return match.parent.absolute()

    # === الأولوية 3: أول نتيجة (حتى لو hebrew) ===
    if all_matches:
        return all_matches[0].parent.absolute()

    return None

PYTHON_DIR = find_arabic_python_dir()

# =============================================
# 4. واجهة المستخدم
# =============================================
st.markdown("""
    <style>
        body { direction: rtl; text-align: right; }
        .stTextArea textarea { direction: rtl; font-size: 18px; }
        .result-box {
            background-color: #f0f8f0;
            padding: 20px;
            border-radius: 10px;
            border: 2px solid #4CAF50;
            direction: rtl;
            font-size: 22px;
            line-height: 2;
        }
    </style>
""", unsafe_allow_html=True)

st.title("📝 مُشكِّل النصوص العربية الذكي")

# =============================================
# 5. التحقق من وجود المحرك
# =============================================
if PYTHON_DIR is None:
    st.error("❌ لم يتم العثور على ملف المحرك diacritize.py!")
    st.info(f"📂 المسار الحالي: `{os.getcwd()}`")
    # عرض هيكل الملفات للمساعدة في التشخيص
    with st.expander("🔍 عرض هيكل الملفات للتشخيص"):
        for root, dirs, files in os.walk(os.getcwd()):
            level = root.replace(os.getcwd(), '').count(os.sep)
            indent = ' ' * 2 * level
            st.text(f'{indent}📁 {os.path.basename(root)}/')
            if level < 3:  # عرض 3 مستويات فقط
                subindent = ' ' * 2 * (level + 1)
                for file in files[:10]:
                    st.text(f'{subindent}📄 {file}')
    st.stop()

# عرض المسار المُكتشف
st.caption(f"✅ تم العثور على المحرك في: `{PYTHON_DIR}`")

# =============================================
# 6. تعريف المسارات
# =============================================
DIACRITIZE_SCRIPT = os.path.join(PYTHON_DIR, "diacritize.py")
WEIGHTS_DIR = os.path.join(PYTHON_DIR, "log_dir", "CA_MSA.base.cbhg", "models")
WEIGHTS_FILE = os.path.join(WEIGHTS_DIR, "2000000-snapshot.pt")
WEIGHTS_URL = "https://github.com/secryst/rababa-models/releases/download/0.1/2000000-snapshot.pt"
CONFIG_FILE = os.path.join(PYTHON_DIR, "config", "cbhg.yml")

# =============================================
# 7. تحميل الأوزان
# =============================================
if not os.path.exists(WEIGHTS_FILE):
    with st.spinner("⏳ جاري تحميل نموذج الذكاء الاصطناعي (مرة واحدة فقط ~200MB)..."):
        os.makedirs(WEIGHTS_DIR, exist_ok=True)
        try:
            urllib.request.urlretrieve(WEIGHTS_URL, WEIGHTS_FILE)
            st.success("✅ تم تحميل النموذج بنجاح!")
        except Exception as e:
            st.error(f"❌ فشل تحميل النموذج: {e}")
            st.stop()

# =============================================
# 8. التحقق من ملف الإعدادات
# =============================================
if not os.path.exists(CONFIG_FILE):
    st.warning(f"⚠️ ملف الإعدادات غير موجود: `{CONFIG_FILE}`")
    # عرض ملفات الإعدادات المتاحة
    config_dir = os.path.join(PYTHON_DIR, "config")
    if os.path.exists(config_dir):
        configs = os.listdir(config_dir)
        st.info(f"ملفات الإعدادات المتاحة: {configs}")

# =============================================
# 9. منطق التشكيل
# =============================================
user_text = st.text_area("✏️ أدخل النص العربي:", height=150, placeholder="اكتب هنا النص الذي تريد تشكيله...")

col1, col2 = st.columns([3, 1])
with col1:
    run_button = st.button("تـشـكـيـل الـنـص 🚀", type="primary", use_container_width=True)
with col2:
    debug_mode = st.checkbox("🔧 تشخيص")

if run_button:
    if not user_text.strip():
        st.warning("⚠️ الرجاء إدخال نص عربي أولاً!")
    else:
        with st.spinner("⏳ جاري تشكيل النص..."):
            # بناء الأمر
            command = [
                sys.executable,
                "diacritize.py",
                "--model_kind", "cbhg",
                "--config", "config/cbhg.yml",
                "--text", user_text
            ]
            # إضافة PYTHONPATH لضمان استيراد الوحدات
            env = os.environ.copy()
            env["PYTHONPATH"] = str(PYTHON_DIR) + os.pathsep + env.get("PYTHONPATH", "")

            if debug_mode:
                st.code(f"الأمر: {' '.join(command)}\nالمجلد: {PYTHON_DIR}", language="bash")

            try:
                result = subprocess.run(
                    command,
                    cwd=str(PYTHON_DIR),
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    env=env,
                    timeout=120      # حد أقصى دقيقتين
                )

                if debug_mode:
                    with st.expander("📋 تفاصيل التشغيل"):
                        st.text(f"Return Code: {result.returncode}")
                        st.text(f"STDOUT:\n{result.stdout}")
                        st.text(f"STDERR:\n{result.stderr}")

                if result.returncode == 0:
                    # استخراج النتيجة من آخر سطر
                    lines = [l.strip() for l in result.stdout.split('\n') if l.strip()]
                    if lines:
                        diacritized_text = lines[-1]
                        st.success("✅ تم التشكيل بنجاح!")
                        st.markdown(
                            f'<div class="result-box">{diacritized_text}</div>',
                            unsafe_allow_html=True
                        )
                        # زر النسخ
                        st.code(diacritized_text, language=None)
                    else:
                        st.warning("⚠️ لم يُرجع المحرك أي نتيجة!")
                else:
                    # ===============================
                    # معالجة الأخطاء الشائعة
                    # ===============================
                    error_msg = result.stderr
                    if "No module named" in error_msg:
                        # استخراج اسم المكتبة الناقصة
                        missing = error_msg.split("No module named")[-1].strip().strip("'\"")
                        st.error(f"❌ مكتبة ناقصة: `{missing}`")
                        st.info("🔄 جاري التثبيت التلقائي...")
                        # تثبيت المكتبة وإعادة المحاولة
                        subprocess.check_call([
                            sys.executable,
                            "-m",
                            "pip",
                            "install",
                            missing,
                            "-q"
                        ])
                        st.success(f"✅ تم تثبيت `{missing}` - اضغط تشكيل مرة أخرى!")
                        st.rerun()
                    elif "CUDA" in error_msg or "cuda" in error_msg:
                        st.error("❌ خطأ GPU - السيرفر يعمل بـ CPU فقط")
                        st.info("تأكد أن الإعدادات تستخدم CPU")
                    else:
                        st.error(f"❌ خطأ من المحرك:")
                        st.code(error_msg, language="bash")
            except subprocess.TimeoutExpired:
                st.error("❌ انتهت المهلة - النص طويل جداً!")
            except Exception as e:
                st.error(f"❌ خطأ نظام: {e}")

# =============================================
# 10. معلومات إضافية
# =============================================
with st.expander("ℹ️ معلومات عن التطبيق"):
    st.markdown("""
        - **المحرك**: Rababa CBHG Model
        - **الوظيفة**: تشكيل النصوص العربية تلقائياً
        - **الدقة**: ~95% على النصوص الفصحى
    """)
    st.text(f"📂 مسار المحرك: {PYTHON_DIR}")
    st.text(f"🐍 Python: {sys.version}")
