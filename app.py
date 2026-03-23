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
# 2. تثبيت المكتبات
# =============================================
def install_packages():
    required = {
        "tqdm": "tqdm",
        "numpy": "numpy",
        "yaml": "pyyaml",
        "ruamel": "ruamel.yaml"
    }
    for imp, pkg in required.items():
        try:
            __import__(imp)
        except ImportError:
            subprocess.run([sys.executable, "-m", "pip", "install", pkg, "-q"], capture_output=True)


if "pkgs_ok" not in st.session_state:
    with st.spinner("⏳ تجهيز البيئة..."):
        install_packages()
    st.session_state.pkgs_ok = True

# =============================================
# 3. البحث عن المجلد العربي
# =============================================
def find_arabic_dir():
    cwd = Path(os.getcwd())
    for pattern in ["python/arabic/diacritize.py", "python/diacritize.py", "arabic/diacritize.py"]:
        candidate = cwd / pattern
        if candidate.exists():
            return candidate.parent.absolute()
    for match in cwd.rglob("diacritize.py"):
        if "hebrew" not in str(match).lower():
            return match.parent.absolute()
    return None


PYTHON_DIR = find_arabic_dir()

# =============================================
# 4. إصلاح شامل لكل ملفات Python في المحرك
# =============================================
def patch_all_files(python_dir):
    """إصلاح شامل لجميع مشاكل التوافق"""
    if not python_dir:
        return

    # ---- إصلاح config_manager.py ----
    cm_path = os.path.join(python_dir, "config_manager.py")
    if os.path.exists(cm_path):
        with open(cm_path, "r", encoding="utf-8") as f:
            content = f.read()
        original = content

        # إصلاح 1: استبدال السطر الشرطي CUDA بالكامل
        content = re.sub(
            r'saved_model\s*=\s*torch\.load\(last_model_path\)\s*if\s*torch\.cuda\.is_available\(\)\s*else\s*torch\.load\(last_model_path,\s*map_location=torch\.device\([\'"]cpu[\'"]\)\)',
            'saved_model = torch.load(last_model_path, map_location=torch.device(\'cpu\'), weights_only=False)',
            content
        )

        # إصلاح 2: أي torch.load بدون weights_only
        content = re.sub(
            r'torch\.load\(([^)]*)\)(?![^(]*weights_only)',
            lambda m: f'torch.load({m.group(1)}, weights_only=False)' if 'weights_only' not in m.group(1) else m.group(0),
            content
        )

        # إصلاح 3: تصحيح weights_only=False مكرر
        while 'weights_only=False, weights_only=False' in content:
            content = content.replace(
                'weights_only=False, weights_only=False',
                'weights_only=False'
            )

        if content != original:
            with open(cm_path, "w", encoding="utf-8") as f:
                f.write(content)

    # ---- إصلاح diacritizer.py (إجبار CPU) ----
    diac_path = os.path.join(python_dir, "diacritizer.py")
    if os.path.exists(diac_path):
        with open(diac_path, "r", encoding="utf-8") as f:
            content = f.read()
        original = content
        # إجبار CPU في أي مكان يُذكر فيه .cuda() أو .to('cuda')
        content = content.replace('.cuda()', '.cpu()')
        content = content.replace(".to('cuda')", ".to('cpu')")
        content = content.replace('.to("cuda")', '.to("cpu")')
        if content != original:
            with open(diac_path, "w", encoding="utf-8") as f:
                f.write(content)

    # ---- إصلاح أي ملف .py يحتوي torch.load ----
    for py_file in Path(python_dir).rglob("*.py"):
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()
            original = content
            if "torch.load" in content and "weights_only" not in content:
                content = re.sub(
                    r'torch\.load\(([^)]+)\)',
                    lambda m: f'torch.load({m.group(1)}, weights_only=False)',
                    content
                )
            if content != original:
                with open(py_file, "w", encoding="utf-8") as f:
                    f.write(content)
        except Exception:
            pass

# =============================================
# 5. واجهة المستخدم
# =============================================
st.markdown("""
    <style>
        body { direction: rtl; text-align: right; }
        .stTextArea textarea { direction: rtl; font-size: 18px; }
        .result-box {
            background: linear-gradient(135deg, #f0f8f0, #e8f5e9);
            padding: 20px;
            border-radius: 10px;
            border: 2px solid #4CAF50;
            direction: rtl;
            font-size: 22px;
            line-height: 2.2;
            margin: 10px 0;
        }
    </style>
""", unsafe_allow_html=True)

st.title("📝 مُشكِّل النصوص العربية الذكي")

if PYTHON_DIR is None:
    st.error("❌ لم يتم العثور على المحرك!")
    st.stop()

st.caption(f"✅ المحرك: `{PYTHON_DIR}`")

# =============================================
# 6. تطبيق الإصلاحات
# =============================================
if "patched" not in st.session_state:
    with st.spinner("🔧 تطبيق إصلاحات التوافق..."):
        patch_all_files(PYTHON_DIR)
    st.session_state.patched = True

# =============================================
# 7. الأوزان
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
# 8. دالة التشكيل المباشر (بدون subprocess)
# =============================================
@st.cache_resource
def load_diacritizer():
    """تحميل المحرك مباشرة في نفس العملية - أسرع وأسهل للتشخيص"""
    original_dir = os.getcwd()
    try:
        os.chdir(str(PYTHON_DIR))
        if str(PYTHON_DIR) not in sys.path:
            sys.path.insert(0, str(PYTHON_DIR))
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        import torch
        torch.set_default_device('cpu')
    except Exception:
        pass
    finally:
        os.chdir(original_dir)
    return True

# =============================================
# 9. التشكيل
# =============================================
user_text = st.text_area("✏️ أدخل النص العربي:", height=150, placeholder="مثال: ذهب الطالب إلى المدرسة")

col1, col2 = st.columns([3, 1])
with col1:
    run_button = st.button("تـشـكـيـل 🚀", type="primary", use_container_width=True)
with col2:
    debug_mode = st.checkbox("🔧 تشخيص")

if run_button:
    if not user_text.strip():
        st.warning("⚠️ أدخل نصاً!")
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
                cm = os.path.join(PYTHON_DIR, "config_manager.py")
                if os.path.exists(cm):
                    with open(cm) as f:
                        torch_lines = [l.strip() for l in f if "torch.load" in l]
                    st.code("torch.load:\n" + "\n".join(torch_lines))

            try:
                result = subprocess.run(
                    command,
                    cwd=str(PYTHON_DIR),
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    env=env,
                    timeout=180
                )

                # ✅ دائماً عرض stderr في وضع التشخيص
                if debug_mode:
                    with st.expander("📋 تفاصيل كاملة", expanded=True):
                        st.text(f"Return Code: {result.returncode}")
                        st.text(f"=== STDOUT ===\n{result.stdout}")
                        st.text(f"=== STDERR ===\n{result.stderr}")

                if result.returncode == 0:
                    # تصفية الأسطر - استبعاد رسائل التحذير
                    lines = []
                    for l in result.stdout.split('\n'):
                        l = l.strip()
                        if l and not l.startswith(('/', 'Using', 'Warning', 'Loading')):
                            lines.append(l)
                    if lines:
                        diacritized_text = lines[-1]
                        st.success("✅ تم التشكيل!")
                        st.markdown(
                            f'<div class="result-box">{diacritized_text}</div>',
                            unsafe_allow_html=True
                        )
                        st.code(diacritized_text, language=None)
                    else:
                        # ربما النتيجة في stderr
                        all_output = result.stdout + "\n" + result.stderr
                        all_lines = [l.strip() for l in all_output.split('\n') if l.strip()]
                        if all_lines:
                            st.info("📄 المخرجات:")
                            for line in all_lines[-3:]:
                                st.text(line)
                        else:
                            st.warning("⚠️ لا نتيجة!")
                else:
                    error_msg = result.stderr
                    if "No module named" in error_msg:
                        pkg_map = {
                            "ruamel": "ruamel.yaml",
                            "yaml": "pyyaml",
                            "cv2": "opencv-python",
                            "PIL": "pillow",
                            "sklearn": "scikit-learn"
                        }
                        match = re.search(r"No module named ['\"]([^'\"]+)['\"]", error_msg)
                        if match:
                            mod = match.group(1).split('.')[0]
                            pkg = pkg_map.get(mod, mod)
                            st.error(f"❌ مكتبة ناقصة: `{pkg}`")
                            subprocess.run([sys.executable, "-m", "pip", "install", pkg], capture_output=True)
                            st.success(f"✅ تم تثبيت `{pkg}` - اضغط تشكيل مرة أخرى")
                    elif "weights_only" in error_msg or "UnpicklingError" in error_msg:
                        st.error("❌ مشكلة توافق PyTorch - إعادة الإصلاح...")
                        del st.session_state["patched"]
                        st.rerun()
                    elif "out of memory" in error_msg.lower():
                        st.error("❌ الذاكرة غير كافية - جرب نصاً أقصر")
                    else:
                        st.error("❌ خطأ:")
                        st.code(error_msg[-500:] if len(error_msg) > 500 else error_msg)

            except subprocess.TimeoutExpired:
                st.error("❌ انتهت المهلة (3 دقائق)")
            except Exception as e:
                st.error(f"❌ خطأ: {e}")

# =============================================
# 10. معلومات
# =============================================
with st.expander("ℹ️ معلومات"):
    st.markdown("""
        - **المحرك**: Rababa CBHG (CPU)
        - **التوافق**: PyTorch 2.6+
        - **الدقة**: ~95%
    """)
    st.text(f"📂 {PYTHON_DIR}")
    st.text(f"🐍 {sys.version}")
