import streamlit as st
import os
import tempfile
import time
from pathlib import Path

# --- Converters ---
from PIL import Image
from pdf2docx import Converter
import sys
import subprocess

# docx2pdf works on Windows (uses Word). On Linux/cloud we use LibreOffice via subprocess.
if sys.platform == "win32":
    try:
        from docx2pdf import convert as _docx2pdf_win
    except ImportError:
        _docx2pdf_win = None
else:
    _docx2pdf_win = None

import pandas as pd
try:
    from moviepy.editor import VideoFileClip, AudioFileClip
except ModuleNotFoundError:
    from moviepy import VideoFileClip, AudioFileClip

# --- Configuration ---
st.set_page_config(
    page_title="Kernel | Universal File Converter",
    page_icon="logo.png" if Path("logo.png").exists() else "�",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Clean Custom CSS ---
custom_css = """
<style>
/* Subtle elegant UI enhancements */
div[data-testid="stSidebar"] {
    background-color: #fafafa;
    border-right: 1px solid #eaeaea;
}
.stButton > button {
    border-radius: 12px;
    font-weight: 600;
    transition: all 0.2s ease-in-out;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}
/* Dark mode responsive sidebar */
@media (prefers-color-scheme: dark) {
    div[data-testid="stSidebar"] {
        background-color: #1a1c23;
    }
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)
import json
import csv
import xmltodict
import yaml
import markdown2
import html2text
import toml

# --- Conversion Logic ---

CONVERSION_MAP = {
    "Image": {
        "formats": ["png", "jpg", "jpeg", "webp", "bmp", "gif", "tiff", "ico", "ppm", "sgi", "tga", "eps", "pcx", "im", "psd", "rgb", "rgba", "mpo"],
    },
    "Document/Text": {
        "formats": ["pdf", "docx", "txt", "md", "html", "rtf", "rst", "cfg", "conf", "env", "log"],
    },
    "Video/Audio": {
        "formats": ["mp4", "avi", "mov", "mkv", "wmv", "flv", "webm", "m4v", "3gp", "ts", "mpeg", "mpg", "vob", "rm", "rmvb", "asf", "mp3", "wav", "ogg", "flac", "aac", "m4a", "wma", "aiff", "alac", "amr"],
    },
    "Data & Configs": {
        "formats": ["csv", "xlsx", "json", "xml", "yaml", "yml", "tsv", "ini", "toml"],
    }
}

def convert_image(in_path: str, out_path: str, target_ext: str):
    """Converts images between various formats."""
    img = Image.open(in_path)
    if img.mode in ("RGBA", "P") and target_ext in ("jpg", "jpeg"):
        img = img.convert("RGB")
    elif target_ext == "png":
        img = img.convert("RGBA")
    img.save(out_path)

def _convert_docx_to_pdf_cloud(in_path: str, out_path: str):
    """
    Converts DOCX to PDF using LibreOffice headless mode.
    Works on Linux / Streamlit Cloud. Requires libreoffice in packages.txt.
    """
    out_dir = str(Path(out_path).parent)
    result = subprocess.run(
        ["libreoffice", "--headless", "--convert-to", "pdf", "--outdir", out_dir, in_path],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(f"LibreOffice conversion failed: {result.stderr}")
    # LibreOffice saves as <original_stem>.pdf in the output directory
    generated = Path(out_dir) / (Path(in_path).stem + ".pdf")
    if generated.exists() and str(generated) != out_path:
        generated.rename(out_path)

def convert_document(in_path: str, out_path: str, target_ext: str, original_ext: str):
    """Converts documents and plain texts/markdown."""
    if original_ext == "pdf" and target_ext == "docx":
        # pdf2docx is pure Python — works everywhere
        cv = Converter(in_path)
        cv.convert(out_path, start=0, end=None)
        cv.close()
    elif original_ext == "docx" and target_ext == "pdf":
        if sys.platform == "win32" and _docx2pdf_win:
            # Use Microsoft Word on Windows for best fidelity
            _docx2pdf_win(in_path, out_path)
        else:
            # Use LibreOffice on Linux / cloud
            _convert_docx_to_pdf_cloud(in_path, out_path)
    elif original_ext == "md" and target_ext == "html":
        with open(in_path, 'r', encoding='utf-8') as f:
            html = markdown2.markdown(f.read())
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html)
    elif original_ext == "html" and target_ext in ["md", "txt"]:
        with open(in_path, 'r', encoding='utf-8') as f:
            text = html2text.html2text(f.read())
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(text)
    elif target_ext in ["txt", "md", "rtf", "html", "rst", "cfg", "conf", "env", "log"]:
        with open(in_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(content)
    else:
        raise ValueError(f"Conversion from {original_ext} to {target_ext} is not supported directly.")

def convert_media(in_path: str, out_path: str, target_ext: str):
    """Extracts audio from video or converts video/audio formats using moviepy."""
    is_audio_out = target_ext in ["mp3", "wav", "ogg", "flac", "aac", "m4a", "wma", "aiff", "alac", "amr"]
    clip = VideoFileClip(in_path) if not in_path.endswith(is_audio_out) else AudioFileClip(in_path)
    
    try:
        if isinstance(clip, VideoFileClip):
            orig_fps = clip.fps or 24
            if is_audio_out:
                clip.audio.write_audiofile(out_path)
            elif target_ext == "gif":
                clip.write_gif(out_path, fps=min(10, orig_fps))
            else:
                # Video to Video
                clip.write_videofile(out_path, codec="libx264", audio_codec="aac")
        else: # Audio to Audio
             clip.write_audiofile(out_path)
    finally:
        clip.close()

def convert_data(in_path: str, out_path: str, target_ext: str, original_ext: str):
    """Converts structured data between CSV, TSV, XLSX, JSON, XML, YAML."""
    data_dict = []
    
    # --- Data Loading ---
    if original_ext in ["csv", "tsv"]:
        sep = '\t' if original_ext == "tsv" else ','
        df = pd.read_csv(in_path, sep=sep)
    elif original_ext == "xlsx":
        df = pd.read_excel(in_path)
    elif original_ext == "json":
        try:
            df = pd.read_json(in_path)
        except Exception:
            # Handle non-tabular json
            with open(in_path, 'r') as f:
                data_dict = json.load(f)
            df = pd.json_normalize(data_dict)
    elif original_ext in ["yaml", "yml"]:
        with open(in_path, 'r') as f:
             data_dict = yaml.safe_load(f)
             if isinstance(data_dict, list):
                 df = pd.DataFrame(data_dict)
             else:
                 df = pd.json_normalize(data_dict)
    elif original_ext == "xml":
        with open(in_path, 'r') as f:
             doc = xmltodict.parse(f.read())
             # Attempt to flatten 
             keys = list(doc.keys())
             if keys:
                 inner = doc[keys[0]]
                 if isinstance(inner, dict):
                     list_key = [k for k in inner.keys() if isinstance(inner[k], list)]
                     if list_key: df = pd.DataFrame(inner[list_key[0]])
                     else: df = pd.json_normalize(inner)
                 else:
                     df = pd.json_normalize(doc)
    elif original_ext == "toml":
        with open(in_path, 'r') as f:
             data_dict = toml.load(f)
             df = pd.json_normalize(data_dict)
    elif original_ext == "ini":
         raise ValueError("INI parsing to tabular is not directly supported.")
    else:
        raise ValueError("Unsupported input data format")
    
    # --- Data Saving ---
    if target_ext == "csv":
        df.to_csv(out_path, index=False)
    elif target_ext == "tsv":
        df.to_csv(out_path, index=False, sep='\t')
    elif target_ext == "xlsx":
        df.to_excel(out_path, index=False)
    elif target_ext == "json":
        df.to_json(out_path, orient="records", indent=4)
    elif target_ext in ["yaml", "yml"]:
        records = df.to_dict(orient="records")
        with open(out_path, 'w') as f:
            yaml.dump(records, f)
    elif target_ext == "xml":
        xml_data = {'root': {'row': df.to_dict(orient="records")}}
        with open(out_path, 'w') as f:
            f.write(xmltodict.unparse(xml_data, pretty=True))
    elif target_ext == "toml":
        records = df.to_dict(orient="records")
        # toml requires string keys and specific nesting, wrapping it in a dict
        with open(out_path, 'w') as f:
            toml.dump({"data": records}, f)
    else:
        raise ValueError("Unsupported output data format")

def compress_image(in_path: str, out_path: str, quality: int):
    """Compresses a JPEG/JPG image to reduce file size."""
    img = Image.open(in_path)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.save(out_path, "JPEG", quality=quality, optimize=True)

def get_category(ext: str):
    """Identifies the file category based on extension."""
    ext = ext.lower().replace('.', '')
    for cat, info in CONVERSION_MAP.items():
        if ext in info["formats"]: 
            return cat
    return None

# --- UI Components ---

# Sidebar for Instructions and Formats
with st.sidebar:
    if Path("logo.png").exists():
        st.image("logo.png", width=64)
    st.markdown("## Kernel")
    st.caption("Universal file converter. 66 formats.")
    st.divider()
    
    with st.expander("How to use", expanded=True):
        st.markdown(
            """
            1. Select a tool from the main tabs (Converter or Compressor).
            2. Upload your file via drag-and-drop.
            3. Choose settings like target format or compression level.
            4. Click the process button.
            5. Download your finished file.
            """
        )
    
    with st.expander("Supported Formats"):
        st.markdown("**18 Image Formats:**")
        st.caption(", ".join(CONVERSION_MAP["Image"]["formats"]))
        st.markdown("**11 Document & Text Formats:**")
        st.caption(", ".join(CONVERSION_MAP["Document/Text"]["formats"]))
        st.markdown("**26 Video & Audio Formats:**")
        st.caption(", ".join(CONVERSION_MAP["Video/Audio"]["formats"]))
        st.markdown("**9 Data & Config Formats:**")
        st.caption(", ".join(CONVERSION_MAP["Data & Configs"]["formats"]))
        st.success("Total supported: 64+ pure formats explicitly handled.")

    st.divider()
    st.markdown("**Sample Files**")
    st.caption("Download these to test the converter.")

    SAMPLE_DIR = Path("sample_files")

    _samples = [
        ("sample_data.csv",     "text/csv"),
        ("sample_data.json",    "application/json"),
        ("sample_document.md",  "text/markdown"),
        ("sample_image.png",    "image/png"),
    ]
    for fname, mime in _samples:
        fpath = SAMPLE_DIR / fname
        if fpath.exists():
            with open(fpath, "rb") as _f:
                st.download_button(
                    label=fname,
                    data=_f.read(),
                    file_name=fname,
                    mime=mime,
                    key=f"sample_{fname}",
                    use_container_width=True,
                )

# Main Header — logo and title aligned with flexbox
import base64

def _img_to_base64(path: str) -> str:
    """Reads a local image file and returns a base64 data URI."""
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    return f"data:image/png;base64,{data}"

if Path("logo.png").exists():
    logo_b64 = _img_to_base64("logo.png")
    st.markdown(
        f"""
        <div style="display:flex; align-items:center; gap:14px; margin-bottom:4px;">
            <img src="{logo_b64}" width="52" style="border-radius:10px; flex-shrink:0;" />
            <span style="font-size:2.4rem; font-weight:700; line-height:1; margin:0;">Kernel</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.title("Kernel")
st.write("Convert files between 66 formats. Drop a file, pick a target, done.")

# Application Tabs
tab1, tab2 = st.tabs(["Universal Converter", "Image Compressor"])

# --- Tab 1: Universal Converter ---
with tab1:
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.subheader("1. Upload File")
        uploaded_file = st.file_uploader("Choose a file to convert", help="Format is auto-detected.", key="converter_upload")
        
    if uploaded_file:
        file_ext = uploaded_file.name.split('.')[-1].lower()
        category = get_category(file_ext)
        
        if not category:
            st.error(f"Format `{file_ext}` is not supported yet.")
        else:
            with col2:
                st.subheader("2. Conversion Settings")
                # Filter out the current extension from target options
                available_formats = [f for f in CONVERSION_MAP[category]["formats"] if f != file_ext]
                
                target_format = st.selectbox("Convert to format:", available_formats)
                
                if st.button("Start Conversion", use_container_width=True, type="primary"):
                    with st.spinner("Processing file..."):
                        try:
                            # 1. Save uploaded file to temp path
                            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tmp_in:
                                tmp_in.write(uploaded_file.getvalue())
                                in_path = tmp_in.name
                                
                            # 2. Determine output path (ensure different from input)
                            out_path = in_path + f"_converted.{target_format}"
                            
                            start_time = time.time()
                            
                            # 3. Route to the correct conversion function
                            if category == "Image":
                                convert_image(in_path, out_path, target_format)
                            elif category == "Document/Text":
                                convert_document(in_path, out_path, target_format, file_ext)
                            elif category == "Video/Audio":
                                convert_media(in_path, out_path, target_format)
                            elif category == "Data & Configs":
                                convert_data(in_path, out_path, target_format, file_ext)
                                
                            end_time = time.time()
                            st.success(f"Conversion successful in {round(end_time - start_time, 2)}s.")
                            
                            # Read converted data to session state to prevent button disappearance
                            with open(out_path, "rb") as f:
                                st.session_state[f"converted_data_{uploaded_file.name}"] = f.read()
                        except Exception as e:
                            st.error(f"An error occurred: {str(e)}")
                            
                # 4. Provide download link outside the button to persist it
                if f"converted_data_{uploaded_file.name}" in st.session_state:
                    st.download_button(
                        label="Download Converted File",
                        data=st.session_state[f"converted_data_{uploaded_file.name}"],
                        file_name=f"{Path(uploaded_file.name).stem}.{target_format}",
                        mime="application/octet-stream",
                        type="primary",
                        key=f"dl_{uploaded_file.name}"
                    )
    else:
        with col2:
            st.info("Upload a file on the left to see available conversion options.")

# --- Tab 2: Image Compressor ---
with tab2:
    st.subheader("Quickly reduce image file sizes")
    st.write("Supported formats: JPG, JPEG, PNG, WEBP, BMP. Output will be compressed as JPEG.")
    
    c_col1, c_col2 = st.columns([1, 1], gap="large")
    
    with c_col1:
        img_upload = st.file_uploader("Upload Image to compress", type=["jpg", "jpeg", "png", "webp", "bmp"], key="compressor_upload")
        
    if img_upload:
        with c_col2:
            st.subheader("Compression Settings")
            quality = st.slider("Quality Level (1-100)", min_value=1, max_value=100, value=70, help="Lower value = smaller file size, but less visual clarity.")
            
            if st.button("Compress Image", use_container_width=True, type="primary"):
                with st.spinner("Compressing..."):
                    try:
                        file_ext = img_upload.name.split('.')[-1].lower()
                        # Input temp file
                        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tmp_in:
                            tmp_in.write(img_upload.getvalue())
                            in_path = tmp_in.name
                            
                        # Compacting always outputs as JPEG for max savings. Ensure different path!
                        out_path = in_path + "_compressed.jpg"
                        
                        start_time = time.time()
                        compress_image(in_path, out_path, quality)
                        end_time = time.time()
                        
                        original_size = len(img_upload.getvalue()) / 1024
                        new_size = os.path.getsize(out_path) / 1024
                        savings = 100 - (new_size / original_size * 100) if original_size > 0 else 0
                        
                        st.success(f"Compression finished in {round(end_time - start_time, 2)}s.")
                        
                        # Show file size metrics
                        m1, m2, m3 = st.columns(3)
                        m1.metric("Original Size", f"{original_size:.1f} KB")
                        m2.metric("New Size", f"{new_size:.1f} KB")
                        m3.metric("Space Saved", f"{savings:.1f}%")
                        
                        # Store in session state to persist download button
                        with open(out_path, "rb") as f:
                            st.session_state[f"compressed_data_{img_upload.name}"] = f.read()

                    except Exception as e:
                        st.error(f"Compression failed: {str(e)}")
                        
            # Persist the download button outside the conversion button scope
            if f"compressed_data_{img_upload.name}" in st.session_state:
                st.download_button(
                    label="Download Compressed Image",
                    data=st.session_state[f"compressed_data_{img_upload.name}"],
                    file_name=f"{Path(img_upload.name).stem}_compressed.jpg",
                    mime="image/jpeg",
                    type="primary",
                    key=f"dl_c_{img_upload.name}"
                )
