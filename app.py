import streamlit as st
import os
import subprocess
import urllib.request
import sys
from pathlib import Path
import re

# =============================================
# 1. إعدادات الصفحة
# =============================================
st.set_page_config(page_title="مُشكِّل النصوص العربية", page_icon="📝")

# =============================================
# 2. تثبيت المكتبات الناقصة تلقائياً
# =============================================
def install_missing_packages():
    """تثبيت المكتبات المطلوبة"""
    required_packages = {
        "tqdm": "tqdm",
        "torch": "torch",
        "numpy": "numpy",
        "yaml": "pyyaml",
        "ruamel": "ruamel.yaml",  # 👈 التصحيح هنا
        "onnxruntime": "onnxruntime"
    }
    for import_name, package_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            st.toast(f"⏳ جاري تثبيت {package_name}...")
            try:
                subprocess.check_call([
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    package_name,
                    "-q"
                ])
            except subprocess.CalledProcessError:
                st.warning(f"⚠️ فشل تثبيت {package_name} - سيتم المحاولة لاحقاً")

# تشغيل التثبيت عند أول تحميل فقط
if "packages_installed" not in st.session_state:
    with st.spinner("⏳ جاري تجهيز البيئة (أول مرة فقط)..."):
        install_missing_packages()
    st.session_state.packages_installed = True

# =============================================
# 3. وظيفة البحث الذكي عن المجلد الصحيح
# =============================================
def find_arabic_python_dir():
    """البحث عن diacritize.py في المجلد العربي"""
    cwd = Path(os.getcwd())

    # الأولوية للمسار العربي
    arabic_patterns = [
        "python/arabic/diacritize.py",
        "python/diacritize.py",
        "arabic/diacritize.py",
    ]
    for pattern in arabic_patterns:
        candidate = cwd / pattern
        if candidate.exists():
            return candidate.parent.absolute()

    # البحث العام مع استبعاد hebrew
    all_matches = list(cwd.rglob("diacritize.py"))
    for match in all_matches:
        if "hebrew" not in str(match).lower():
            return match.parent.absolute()

    return all_matches[0].parent.absolute() if all_matches else None

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
    st.stop()

st.caption(f"✅ تم العثور على المحرك في: `{PYTHON_DIR}`")

# =============================================
# 6. تعريف المسارات
# =============================================
DIACRITIZE_SCRIPT = os.path.join(PYTHON_DIR, "diacritize.py")
WEIGHTS_DIR = os.path.join(PYTHON_DIR, "log_dir", "CA_MSA.base.cbhg", "models")
WEIGHTS_FILE = os.path.join(WEIGHTS_DIR, "2000000-snapshot.pt")
WEIGHTS_URL = "https://github.com/secryst/rababa-models/releases/download/0.1/2000000-snapshot.pt"

# =============================================
# 7. تحميل الأوزان
# =============================================
if not os.path.exists(WEIGHTS_FILE):
    with st.spinner("⏳ جاري تحميل نموذج الذكاء الاصطناعي (~200MB)..."):
        os.makedirs(WEIGHTS_DIR, exist_ok=True)
        try:
            urllib.request.urlretrieve(WEIGHTS_URL, WEIGHTS_FILE)
            st.success("✅ تم تحميل النموذج!")
        except Exception as e:
            st.error(f"❌ فشل التحميل: {e}")
            st.stop()

# =============================================
# 8. دالة استخراج اسم المكتبة الصحيح
# =============================================
def extract_package_name(error_message):
    """ استخراج اسم الحزمة الصحيح من رسالة الخطأ مع معالجة الحالات الخاصة """
    # خريطة الأسماء المعروفة
    package_map = {
        "ruamel": "ruamel.yaml",
        "yaml": "pyyaml",
        "cv2": "opencv-python",
        "PIL": "pillow",
        "sklearn": "scikit-learn"
    }
    # استخراج اسم المكتبة من الرسالة
    match = re.search(r"No module named ['\"]([^'\"]+)['\"]", error_message)
    if match:
        module_name = match.group(1).split('.')[0]  # أخذ الجزء الأول فقط
        return package_map.get(module_name, module_name)
    return None

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
            command = [
                sys.executable,
                "diacritize.py",
                "--model_kind", "cbhg",
                "--config", "config/cbhg.yml",
                "--text", user_text
            ]
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
                    timeout=120
                )

                if debug_mode:
                    with st.expander("📋 تفاصيل التشغيل"):
                        st.text(f"Return Code: {result.returncode}")
                        st.text(f"STDOUT:\n{result.stdout}")
                        st.text(f"STDERR:\n{result.stderr}")

                if result.returncode == 0:
                    lines = [l.strip() for l in result.stdout.split('\n') if l.strip()]
                    if lines:
                        diacritized_text = lines[-1]
                        st.success("✅ تم التشكيل بنجاح!")
                        st.markdown(
                            f'<div class="result-box">{diacritized_text}</div>',
                            unsafe_allow_html=True
                        )
                        st.code(diacritized_text, language=None)
                    else:
                        st.warning("⚠️ لم يُرجع المحرك أي نتيجة!")
                else:
                    error_msg = result.stderr

                    # ===============================
                    # معالجة خطأ المكتبة الناقصة
                    # ===============================
                    if "No module named" in error_msg:
                        package_name = extract_package_name(error_msg)
                        if package_name:
                            st.error(f"❌ مكتبة ناقصة: `{package_name}`")
                            st.info("🔄 جاري التثبيت التلقائي...")
                            try:
                                # التثبيت مع عرض التقدم
                                install_result = subprocess.run(
                                    [sys.executable, "-m", "pip", "install", package_name],
                                    capture_output=True,
                                    text=True
                                )
                                if install_result.returncode == 0:
                                    st.success(f"✅ تم تثبيت `{package_name}` بنجاح!")
                                    st.info("🔄 اضغط 'تشكيل النص' مرة أخرى")
                                    st.session_state.packages_installed = False
                                else:
                                    st.error(f"❌ فشل التثبيت:")
                                    st.code(install_result.stderr, language="bash")
                                    st.warning("💡 أضف هذه المكتبة إلى requirements.txt:")
                                    st.code(package_name)
                            except Exception as install_error:
                                st.error(f"❌ خطأ أثناء التثبيت: {install_error}")
                        else:
                            st.error("❌ لم يتم التعرف على المكتبة الناقصة:")
                            st.code(error_msg, language="bash")
                    elif "CUDA" in error_msg or "cuda" in error_msg:
                        st.error("❌ خطأ GPU - السيرفر يعمل بـ CPU فقط")
                    else:
                        st.error(f"❌ خطأ من المحرك:")
                        st.code(error_msg, language="bash")

            except subprocess.TimeoutExpired:
                st.error("❌ انتهت المهلة - النص طويل جداً!")
            except Exception as e:
                st.error(f"❌ خطأ نظام: {e}")
                import traceback
                st.code(traceback.format_exc(), language="python")

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
    st.text(f"🐍 Python: {sys.version}")                    # معالجة الأخطاء الشائعة
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
