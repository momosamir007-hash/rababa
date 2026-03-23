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
# 2. تثبيت المكتبات الناقصة
# =============================================
def install_missing_packages():
    """تثبيت المكتبات المطلوبة"""
    required_packages = {
        "tqdm": "tqdm",
        "numpy": "numpy",
        "yaml": "pyyaml",
        "ruamel": "ruamel.yaml"
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
                pass

if "packages_installed" not in st.session_state:
    with st.spinner("⏳ جاري تجهيز البيئة..."):
        install_missing_packages()
    st.session_state.packages_installed = True

# =============================================
# 3. البحث عن المجلد العربي
# =============================================
def find_arabic_python_dir():
    cwd = Path(os.getcwd())
    arabic_patterns = [
        "python/arabic/diacritize.py",
        "python/diacritize.py",
        "arabic/diacritize.py",
    ]
    for pattern in arabic_patterns:
        candidate = cwd / pattern
        if candidate.exists():
            return candidate.parent.absolute()
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
# 5. التحقق من المحرك
# =============================================
if PYTHON_DIR is None:
    st.error("❌ لم يتم العثور على ملف المحرك!")
    st.stop()

st.caption(f"✅ المحرك: `{PYTHON_DIR}`")

# =============================================
# 6. المسارات
# =============================================
DIACRITIZE_SCRIPT = os.path.join(PYTHON_DIR, "diacritize.py")
WEIGHTS_DIR = os.path.join(PYTHON_DIR, "log_dir", "CA_MSA.base.cbhg", "models")
WEIGHTS_FILE = os.path.join(WEIGHTS_DIR, "2000000-snapshot.pt")
WEIGHTS_URL = "https://github.com/secryst/rababa-models/releases/download/0.1/2000000-snapshot.pt"

# =============================================
# 7. تحميل الأوزان
# =============================================
if not os.path.exists(WEIGHTS_FILE):
    with st.spinner("⏳ تحميل النموذج (~200MB)..."):
        os.makedirs(WEIGHTS_DIR, exist_ok=True)
        try:
            urllib.request.urlretrieve(WEIGHTS_URL, WEIGHTS_FILE)
            st.success("✅ تم التحميل!")
        except Exception as e:
            st.error(f"❌ فشل: {e}")
            st.stop()

# =============================================
# 8. استخراج اسم المكتبة
# =============================================
def extract_package_name(error_message):
    package_map = {
        "ruamel": "ruamel.yaml",
        "yaml": "pyyaml",
        "cv2": "opencv-python",
        "PIL": "pillow",
        "sklearn": "scikit-learn"
    }
    match = re.search(r"No module named ['\"]([^'\"]+)['\"]", error_message)
    if match:
        module_name = match.group(1).split('.')[0]
        return package_map.get(module_name, module_name)
    return None

# =============================================
# 9. التشكيل
# =============================================
user_text = st.text_area("✏️ أدخل النص العربي:", height=150, placeholder="اكتب هنا...")

col1, col2 = st.columns([3, 1])
with col1:
    run_button = st.button("تـشـكـيـل 🚀", type="primary", use_container_width=True)
with col2:
    debug_mode = st.checkbox("🔧 تشخيص")

if run_button:
    if not user_text.strip():
        st.warning("⚠️ أدخل نصاً أولاً!")
    else:
        with st.spinner("⏳ جاري التشكيل..."):
            command = [
                sys.executable,
                "diacritize.py",
                "--model_kind", "cbhg",
                "--config", "config/cbhg.yml",
                "--text", user_text
            ]
            # 👇 إجبار PyTorch على استخدام CPU
            env = os.environ.copy()
            env["PYTHONPATH"] = str(PYTHON_DIR) + os.pathsep + env.get("PYTHONPATH", "")
            env["CUDA_VISIBLE_DEVICES"] = ""   # ✅ تعطيل GPU
            env["OMP_NUM_THREADS"] = "4"       # ✅ تحسين CPU

            if debug_mode:
                st.code(f"الأمر: {' '.join(command)}\nالمجلد: {PYTHON_DIR}")

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
                    with st.expander("📋 تفاصيل"):
                        st.text(f"Return Code: {result.returncode}")
                        st.text(f"STDOUT:\n{result.stdout}")
                        st.text(f"STDERR:\n{result.stderr}")

                if result.returncode == 0:
                    lines = [l.strip() for l in result.stdout.split('\n') if l.strip()]
                    if lines:
                        diacritized_text = lines[-1]
                        st.success("✅ تم التشكيل!")
                        st.markdown(
                            f'<div class="result-box">{diacritized_text}</div>',
                            unsafe_allow_html=True
                        )
                        st.code(diacritized_text, language=None)
                    else:
                        st.warning("⚠️ لا نتيجة!")
                else:
                    error_msg = result.stderr
                    if "No module named" in error_msg:
                        package_name = extract_package_name(error_msg)
                        if package_name:
                            st.error(f"❌ مكتبة ناقصة: `{package_name}`")
                            with st.spinner(f"⏳ تثبيت {package_name}..."):
                                install_result = subprocess.run(
                                    [sys.executable, "-m", "pip", "install", package_name],
                                    capture_output=True,
                                    text=True
                                )
                                if install_result.returncode == 0:
                                    st.success(f"✅ تم تثبيت `{package_name}`!")
                                    st.info("🔄 اضغط 'تشكيل' مرة أخرى")
                                else:
                                    st.error("❌ فشل التثبيت:")
                                    st.code(install_result.stderr)
                        else:
                            st.error("❌ خطأ غير معروف:")
                            st.code(error_msg)
                    elif "CUDA" in error_msg or "cuda" in error_msg:
                        st.error("❌ خطأ GPU (يعمل الآن على CPU)")
                        st.code(error_msg)
                    else:
                        st.error("❌ خطأ:")
                        st.code(error_msg)

            except subprocess.TimeoutExpired:
                st.error("❌ انتهت المهلة!")
            except Exception as e:
                st.error(f"❌ خطأ: {e}")
                if debug_mode:
                    import traceback
                    st.code(traceback.format_exc())

# =============================================
# 10. معلومات
# =============================================
with st.expander("ℹ️ معلومات"):
    st.markdown("""
        - **المحرك**: Rababa CBHG
        - **الوضع**: CPU فقط (Streamlit Cloud)
        - **الدقة**: ~95% على الفصحى
    """)
    st.text(f"📂 {PYTHON_DIR}")
    st.text(f"🐍 {sys.version}")
