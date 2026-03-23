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
# 4. ✅ إصلاح مشكلة PyTorch 2.6 تلقائياً
# =============================================
def patch_torch_load(python_dir):
    """ تعديل config_manager.py لإضافة weights_only=False لحل مشكلة PyTorch 2.6 الجديدة """
    config_manager_path = os.path.join(python_dir, "config_manager.py")
    if not os.path.exists(config_manager_path):
        return False
    with open(config_manager_path, "r", encoding="utf-8") as f:
        content = f.read()
    # التحقق هل تم التعديل سابقاً
    if "weights_only=False" in content:
        return True   # تم التعديل مسبقاً
    # =============================================
    # التعديل 1: إصلاح torch.load العادي
    # من: torch.load(path)
    # إلى: torch.load(path, weights_only=False)
    # =============================================
    # نمط 1: torch.load(last_model_path)
    content = content.replace(
        "torch.load(last_model_path)",
        "torch.load(last_model_path, weights_only=False)"
    )
    # نمط 2: torch.load(last_model_path, map_location=torch.device('cpu'))
    content = content.replace(
        "torch.load(last_model_path, map_location=torch.device('cpu'))",
        "torch.load(last_model_path, map_location=torch.device('cpu'), weights_only=False)"
    )
    # نمط 3: أي torch.load آخر بدون weights_only
    # باستخدام regex للحالات الأخرى
    content = re.sub(
        r"torch\.load\(([^)]+)\)(?!.*weights_only)",
        lambda m: f"torch.load({m.group(1)}, weights_only=False)" if "weights_only" not in m.group(1) else m.group(0),
        content
    )
    # حفظ الملف المعدل
    with open(config_manager_path, "w", encoding="utf-8") as f:
        f.write(content)
    return True

# =============================================
# 5. ✅ إصلاح إضافي: إجبار CPU في config_manager.py
# =============================================
def patch_force_cpu(python_dir):
    """ تعديل config_manager.py لإجبار CPU دائماً """
    config_manager_path = os.path.join(python_dir, "config_manager.py")
    if not os.path.exists(config_manager_path):
        return False
    with open(config_manager_path, "r", encoding="utf-8") as f:
        content = f.read()
    if "# FORCE_CPU_PATCHED" in content:
        return True
    # استبدال السطر الشرطي بسطر CPU مباشر
    old_pattern = (
        "saved_model = torch.load(last_model_path) "
        "if torch.cuda.is_available() else "
        "torch.load(last_model_path, map_location=torch.device('cpu'))"
    )
    new_code = (
        "# FORCE_CPU_PATCHED\n"
        " saved_model = torch.load("
        "last_model_path, "
        "map_location=torch.device('cpu'), "
        "weights_only=False)"
    )
    if old_pattern in content:
        content = content.replace(old_pattern, new_code)
        with open(config_manager_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    return False

# =============================================
# 6. واجهة المستخدم
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
# 7. التحقق من المحرك
# =============================================
if PYTHON_DIR is None:
    st.error("❌ لم يتم العثور على ملف المحرك!")
    st.stop()

st.caption(f"✅ المحرك: `{PYTHON_DIR}`")

# =============================================
# 8. تطبيق الإصلاحات
# =============================================
if "patches_applied" not in st.session_state:
    with st.spinner("🔧 تطبيق إصلاحات التوافق..."):
        patch1 = patch_force_cpu(PYTHON_DIR)
        patch2 = patch_torch_load(PYTHON_DIR)
        if patch1 or patch2:
            st.toast("✅ تم تطبيق إصلاحات التوافق")
    st.session_state.patches_applied = True

# =============================================
# 9. المسارات والأوزان
# =============================================
WEIGHTS_DIR = os.path.join(PYTHON_DIR, "log_dir", "CA_MSA.base.cbhg", "models")
WEIGHTS_FILE = os.path.join(WEIGHTS_DIR, "2000000-snapshot.pt")
WEIGHTS_URL = "https://github.com/secryst/rababa-models/releases/download/0.1/2000000-snapshot.pt"

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
# 10. استخراج اسم المكتبة الناقصة
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
# 11. التشكيل
# =============================================
user_text = st.text_area("✏️ أدخل النص العربي:", height=150, placeholder="اكتب هنا النص العربي...")

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
            env = os.environ.copy()
            env["PYTHONPATH"] = str(PYTHON_DIR) + os.pathsep + env.get("PYTHONPATH", "")
            env["CUDA_VISIBLE_DEVICES"] = ""
            env["OMP_NUM_THREADS"] = "4"

            if debug_mode:
                st.code(f"الأمر: {' '.join(command)}\nالمجلد: {PYTHON_DIR}")
                # عرض محتوى config_manager.py المعدل
                cm_path = os.path.join(PYTHON_DIR, "config_manager.py")
                if os.path.exists(cm_path):
                    with open(cm_path, "r") as f:
                        lines = f.readlines()
                    # عرض الأسطر التي تحتوي torch.load
                    relevant = [l.strip() for l in lines if "torch.load" in l]
                    st.code("torch.load lines:\n" + "\n".join(relevant))

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
                            st.error("❌ خطأ:")
                            st.code(error_msg)
                    elif "weights_only" in error_msg or "UnpicklingError" in error_msg:
                        st.error("❌ مشكلة توافق PyTorch - إعادة تطبيق الإصلاح...")
                        st.session_state.patches_applied = False
                        st.rerun()
                    else:
                        st.error("❌ خطأ:")
                        st.code(error_msg)

            except subprocess.TimeoutExpired:
                st.error("❌ انتهت المهلة!")
            except Exception as e:
                st.error(f"❌ خطأ: {e}")

# =============================================
# 12. معلومات
# =============================================
with st.expander("ℹ️ معلومات"):
    st.markdown("""
        - **المحرك**: Rababa CBHG (CPU Mode)
        - **PyTorch**: متوافق مع 2.6+
        - **الدقة**: ~95% على الفصحى
    """)
    st.text(f"📂 {PYTHON_DIR}")
    st.text(f"🐍 {sys.version}")
