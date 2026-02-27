<p align="center">
  <img src="logo.png" alt="Kernel Logo" width="80" />
</p>

<h1 align="center">Kernel</h1>
<p align="center">Universal file converter. 66 formats. Zero cloud uploads.</p>

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.9+-3776AB?style=flat&logo=python&logoColor=white" /></a>
  <a href="https://streamlit.io/"><img src="https://img.shields.io/badge/Streamlit-1.x-FF4B4B?style=flat&logo=streamlit&logoColor=white" /></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green?style=flat" /></a>
</p>

---

**Live App:** [Insert your deployed link here]

> The hosted app runs on Streamlit Cloud and may take 10-20 seconds to wake up if it has been idle. This is expected behavior — the platform spins down free-tier apps after a period of inactivity.

---

## What it does

Kernel is a browser-based file utility. You drag and drop a file, choose what you want it to become, and download the result. No accounts, no data collection, no external servers. Everything is processed on the machine running the app.

It handles four categories of conversion:

- **Images** — change format, preserve quality
- **Documents & Text** — convert between PDF, DOCX, Markdown, HTML, and plain text
- **Video & Audio** — extract audio from video, change container formats
- **Data & Configs** — move data between spreadsheet, JSON, XML, YAML, and TOML formats

It also has a dedicated **Image Compressor** tab with a quality slider and real-time file size savings metrics.

---

## Supported Formats

| Category | Count | Formats |
|---|---|---|
| Image | 18 | png, jpg, jpeg, webp, bmp, gif, tiff, ico, ppm, sgi, tga, eps, pcx, im, psd, rgb, rgba, mpo |
| Document / Text | 11 | pdf, docx, txt, md, html, rtf, rst, cfg, conf, env, log |
| Video & Audio | 26 | mp4, avi, mov, mkv, wmv, flv, webm, m4v, 3gp, ts, mpeg, mpg, vob, rm, rmvb, asf + mp3, wav, ogg, flac, aac, m4a, wma, aiff, alac, amr |
| Data & Configs | 9 | csv, xlsx, json, xml, yaml, yml, tsv, ini, toml |

**Total: 64 distinct formats**

---

## Tech Stack

| Layer | Library | Purpose |
|---|---|---|
| UI | [Streamlit](https://streamlit.io/) | Web framework and component library |
| Images | [Pillow](https://python-pillow.org/) | Read and write 18 image formats |
| PDF → DOCX | [pdf2docx](https://github.com/dothinking/pdf2docx) | Pure Python PDF parsing |
| DOCX → PDF (Windows) | [docx2pdf](https://github.com/AlJohri/docx2pdf) | Uses Microsoft Word locally |
| DOCX → PDF (Linux / Cloud) | LibreOffice (subprocess) | Headless conversion via `packages.txt` |
| Video & Audio | [MoviePy](https://zulko.github.io/moviepy/) | Video processing and audio extraction |
| Data | [pandas](https://pandas.pydata.org/) | Read and write tabular formats |
| Excel | [openpyxl](https://openpyxl.readthedocs.io/) | XLSX read/write engine |
| Markdown | [markdown2](https://github.com/trentm/python-markdown2) | Markdown to HTML conversion |
| HTML | [html2text](https://github.com/Alir3z4/html2text/) | HTML to plain text conversion |
| XML | [xmltodict](https://github.com/martinblech/xmltodict) | XML parsing and generation |
| YAML | [PyYAML](https://pyyaml.org/) | YAML read/write |
| TOML | [toml](https://github.com/uiri/toml) | TOML read/write |

---

## Project Structure

```
kernel/
├── app.py              # The entire application — UI and conversion logic
├── requirements.txt    # Python dependencies (pip)
├── packages.txt        # System dependencies for Streamlit Cloud (LibreOffice)
├── logo.png            # App icon — shown in browser tab, sidebar, and README
├── README.md           # This file
└── sample_files/       # Downloadable test files available inside the app
    ├── sample_data.csv
    ├── sample_data.json
    ├── sample_document.md
    └── sample_image.png
```

> Do not commit `venv/`, `__pycache__/`, or `test_files/` to the repository.

---

## Running locally

Requires Python 3.9 or higher.

```bash
# 1. Clone or download the folder

# 2. Create and activate a virtual environment
python -m venv venv

# Windows
.\venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the app
streamlit run app.py
```

The app opens at `http://localhost:8501`.

---

## Deploying to Streamlit Community Cloud

Streamlit Community Cloud is free and is the recommended deployment target for this app.

1. Push the project to a GitHub repository (public or private).
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **New app**, select your repository, set the branch, and confirm `app.py` as the main file.
4. Click **Deploy**.

Streamlit reads `requirements.txt` for Python packages and `packages.txt` for system packages. LibreOffice is listed in `packages.txt` so DOCX to PDF conversion works on the cloud without Microsoft Word.

Your app will be available at `https://your-app-name.streamlit.app`.

---

## Notes

| Situation | Detail |
|---|---|
| DOCX → PDF fails locally | Requires Microsoft Word on Windows. Works automatically on cloud via LibreOffice. |
| Large video files | Audio extraction from long videos can take 1-2 minutes. The spinner will show while it processes. |
| Rare video codecs (rm, rmvb, vob) | Require ffmpeg installed locally. Works on Streamlit Cloud by default. |
| First load on hosted version | May take 10-20 seconds to wake from sleep mode. |

---

Built with Python and Streamlit.
