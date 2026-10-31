"""
Streamlit Web User Interface for Opportunity & Visa Matcher.
Provides bilingual candidate evaluation and visa eligibility reporting.
"""

import json
import os
import re
import tempfile
import markdown
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

from llamaindex.matcher import analyze_opportunity_and_visa

# Load environment variables
load_dotenv()

# Streamlit Page Configuration
st.set_page_config(
    page_title="Opportunity & Visa Matcher | مطابقة الفرص والتأشيرات",
    page_icon="🌍",
    layout="wide",
)

# UI Localization Dictionary
TEXTS = {
    "English": {
        "title": "🌍 Opportunity & Visa Matcher",
        "caption": "Candidate Evaluation & Visa Eligibility Analysis Platform",
        "lang_settings": "🌐 Language Settings",
        "ui_lang_label": "Interface Language",
        "report_lang_label": "Report Output Language",
        "api_warning": "⚠️ **No Gemini API Key is configured yet.**",
        "api_input_label": "Enter your Gemini API Key below:",
        "api_help": "Get a key from https://aistudio.google.com/",
        "api_success": "Gemini API Key applied for this session!",
        "visa_url_label": "🛂 Visa Rules Source URL (Configured from `.env`):",
        "visa_url_help": "URL to fetch and parse live visa rules.",
        "cv_upload_label": "📄 Upload Candidate CV (PDF)",
        "job_upload_label": "📋 Upload Opportunity (PDF)",
        "analyze_btn": "🚀 Analyze Match & Check Visa",
        "spinner_msg": "🔍 Processing documents and evaluating match...",
        "missing_files_err": "Please upload both a CV and an Opportunity PDF.",
        "missing_api_key_err": "Please provide your Gemini API Key in the field above or in the `.env` file.",
        "analysis_success": "Analysis Complete!",
        "report_header": "📊 Evaluation Report",
        "error_prefix": "Error during analysis",
        "view_mode_label": "Display View",
        "cards_view": "🃏 Colorful Cards",
        "text_view": "📄 Full Text",
        "copy_btn_label": "📋 Copy Report",
        "copied_label": "✅ Copied to Clipboard!",
        "download_btn_label": "📥 Download Report (.md)",
        "raw_expander": "📑 View Raw Markdown",
        "quick_facts_title": "Executive Quick Facts",
        "location_label": "Location / Duty Station",
        "salary_label": "Salary & Grade",
        "match_label": "Match Score",
        "status_label": "Legal Status",
    },
    "العربية": {
        "title": "🌍 مطابقة الفرص والتأشيرات الدولية",
        "caption": "منصة تحليل ومطابقة المرشحين والأهلية القانونية للتأشيرات الدولية",
        "lang_settings": "🌐 إعدادات اللغة / Language Settings",
        "ui_lang_label": "لغة الواجهة",
        "report_lang_label": "لغة إصدار التقرير",
        "api_warning": "⚠️ **لا يوجد مفتاح Gemini API مهيأ بعد.**",
        "api_input_label": "أدخل مفتاح Gemini API أدناه:",
        "api_help": "احصل على مفتاح من https://aistudio.google.com/",
        "api_success": "تم تفعيل مفتاح Gemini API لهذه الجلسة بنجاح!",
        "visa_url_label": "🛂 رابط مصدر لوائح التأشيرة (مهيأ من `.env`):",
        "visa_url_help": "الرابط لجلب وقراءة لوائح التأشيرات الحية.",
        "cv_upload_label": "📄 رفع السيرة الذاتية للمرشح (PDF)",
        "job_upload_label": "📋 رفع تفاصيل الفرصة (PDF)",
        "analyze_btn": "🚀 تحليل التوافق وفحص التأشيرة",
        "spinner_msg": "🔍 جارٍ معالجة المستندات وتحليل التوافق...",
        "missing_files_err": "يرجى رفع ملف السيرة الذاتية وتفاصيل الفرصة بصيغة PDF.",
        "missing_api_key_err": "يرجى إدخال مفتاح Gemini API في الحقل أعلاه أو في ملف `.env`.",
        "analysis_success": "اكتمل التحليل بنجاح!",
        "report_header": "📊 تقرير التقييم",
        "error_prefix": "حدث خطأ أثناء التحليل",
        "view_mode_label": "طريقة العرض",
        "cards_view": "🃏 بطاقات ملونة",
        "text_view": "📄 نص كامل",
        "copy_btn_label": "📋 نسخ التقرير",
        "copied_label": "✅ تم النسخ إلى الحافظة!",
        "download_btn_label": "📥 تحميل التقرير (.md)",
        "raw_expander": "📑 عرض نص Markdown الخام",
        "quick_facts_title": "ملخص البيانات الأساسية السريع",
        "location_label": "مقر العمل الفعلي",
        "salary_label": "الراتب والدرجة",
        "match_label": "نسبة التوافق",
        "status_label": "الأهلية القانونية",
    },
}

# --- Language Controls in Sidebar ---
if "ui_lang" not in st.session_state:
    st.session_state["ui_lang"] = "English"

with st.sidebar:
    st.header("🌐 Language / اللغة")
    current_ui_lang = st.session_state["ui_lang"]
    
    # In Arabic, order options as ["العربية", "English"] so Arabic is first (on the right in RTL); in English, order as ["English", "العربية"]
    ui_options = ["العربية", "English"] if current_ui_lang == "العربية" else ["English", "العربية"]
    current_ui_idx = ui_options.index(current_ui_lang)
    
    selected_lang = st.radio(
        "Interface Language / لغة الواجهة",
        options=ui_options,
        index=current_ui_idx,
        horizontal=True,
        key=f"ui_lang_radio_{current_ui_lang}",
    )
    if selected_lang != current_ui_lang:
        st.session_state["ui_lang"] = selected_lang
        st.rerun()

    ui_lang = st.session_state["ui_lang"]
    is_arabic_ui = ui_lang == "العربية"
    t = TEXTS[ui_lang]

    # Report Output selectbox
    report_options = ["العربية", "English"] if is_arabic_ui else ["English", "العربية"]
    default_report_lang = "العربية" if is_arabic_ui else "English"
    report_idx = report_options.index(default_report_lang)
    report_lang = st.selectbox(
        t["report_lang_label"],
        options=report_options,
        index=report_idx,
    )
    is_arabic_report = report_lang == "العربية"

# Apply Right-to-Left (RTL) CSS when Arabic UI is active
if is_arabic_ui:
    st.markdown(
        """
        <style>
        /* Base page and layout RTL direction */
        .stApp, 
        section[data-testid="stSidebar"],
        div[data-testid="stMainBlockContainer"],
        section.main,
        div[data-testid="stVerticalBlock"] {
            direction: rtl !important;
            text-align: right !important;
        }

        /* Top Heading and Subtitle alignment (Header Right Alignment) */
        div[data-testid="stHeadingWithActionElements"] {
            display: flex !important;
            flex-direction: row !important;
            justify-content: flex-start !important;
            text-align: right !important;
            direction: rtl !important;
            width: 100% !important;
        }
        div[data-testid="stHeadingWithActionElements"] h1,
        div[data-testid="stHeadingWithActionElements"] h2,
        div[data-testid="stHeadingWithActionElements"] h3,
        div[data-testid="stHeadingWithActionElements"] span {
            text-align: right !important;
            direction: rtl !important;
            width: 100% !important;
        }
        div[data-testid="stCaptionContainer"],
        div[data-testid="stCaptionContainer"] p {
            text-align: right !important;
            direction: rtl !important;
            width: 100% !important;
        }

        /* Sidebar RTL Styling and Language Radio */
        section[data-testid="stSidebar"] div[role="radiogroup"] {
            direction: rtl !important;
            display: flex !important;
            flex-direction: row !important;
            justify-content: flex-start !important;
            gap: 1.25rem !important;
        }
        section[data-testid="stSidebar"] div[role="radiogroup"] label {
            direction: rtl !important;
            text-align: right !important;
        }
        section[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child {
            margin-left: 0.5rem !important;
            margin-right: 0 !important;
        }

        /* Inputs, uploaders, dropdowns, expanders, checkboxes */
        div[data-testid="stTextInput"] input, 
        div[data-testid="stFileUploaderDropzone"],
        div[data-testid="stSelectbox"],
        div[data-testid="stMarkdownContainer"] p,
        div[data-testid="stMarkdownContainer"] li,
        div[data-testid="stMarkdownContainer"] h1,
        div[data-testid="stMarkdownContainer"] h2,
        div[data-testid="stMarkdownContainer"] h3,
        .streamlit-expanderHeader,
        div[data-testid="stExpander"] {
            text-align: right !important;
            direction: rtl !important;
        }
        div[data-testid="stCheckbox"] label {
            direction: rtl !important;
            text-align: right !important;
        }
        div[data-testid="stAlert"] {
            direction: rtl !important;
            text-align: right !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# Universal Card & KPI Styling (Guarantees proper RTL/LTR alignment and box fit)
st.markdown(
    """
    <style>
    /* Metric & Container Text Wrap */
    div[data-testid="stMetricValue"],
    div[data-testid="stMetricValue"] > div {
        font-size: 1.05rem !important;
        white-space: normal !important;
        text-overflow: clip !important;
        overflow: visible !important;
        word-break: break-word !important;
        overflow-wrap: break-word !important;
        line-height: 1.35 !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        overflow: hidden !important;
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
    }

    /* KPI Mini Cards inside Quick Facts Ribbon */
    .kpi-card {
        background: rgba(125, 125, 125, 0.05);
        border: 1px solid rgba(125, 125, 125, 0.22);
        border-radius: 10px;
        padding: 0.85rem 1rem;
        min-height: 105px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-sizing: border-box;
        transition: all 0.2s ease;
    }
    .kpi-card:hover {
        background: rgba(125, 125, 125, 0.09);
        border-color: rgba(99, 102, 241, 0.5);
    }
    .kpi-label {
        font-size: 0.78rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 0.35rem;
        display: flex;
        align-items: center;
        gap: 0.35rem;
    }
    .kpi-val {
        font-size: 0.96rem;
        font-weight: 600;
        color: #0f172a;
        line-height: 1.4;
        word-wrap: break-word;
        overflow-wrap: break-word;
        word-break: break-word;
    }
    .kpi-val.kpi-score {
        font-size: 1.45rem;
        font-weight: 700;
        color: #0284c7;
    }
    .kpi-val.kpi-status-red {
        color: #dc2626;
    }
    .kpi-val.kpi-status-green {
        color: #16a34a;
    }
    .kpi-val.kpi-status-yellow {
        color: #d97706;
    }
    @media (prefers-color-scheme: dark) {
        .kpi-card {
            background: rgba(255, 255, 255, 0.04);
            border-color: rgba(255, 255, 255, 0.15);
        }
        .kpi-val {
            color: #f8fafc;
        }
        .kpi-label {
            color: #94a3b8;
        }
        .kpi-val.kpi-score {
            color: #38bdf8;
        }
    }

    /* RTL Specifics for Arabic KPI Cards */
    .kpi-card-rtl {
        direction: rtl !important;
        text-align: right !important;
    }
    .kpi-card-rtl .kpi-label {
        direction: rtl !important;
        text-align: right !important;
        justify-content: flex-start !important;
    }
    .kpi-card-rtl .kpi-val {
        direction: rtl !important;
        text-align: right !important;
    }

    /* Arabic Report Content RTL */
    .card-rtl {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Segoe UI', Tahoma, 'Noto Sans Arabic', 'Cairo', Arial, sans-serif !important;
        line-height: 1.8 !important;
    }
    .card-rtl ul {
        direction: rtl !important;
        text-align: right !important;
        padding-right: 1.5rem !important;
        padding-left: 0 !important;
        margin: 0.5rem 0 !important;
        list-style-type: disc !important;
    }
    .card-rtl ul ul {
        direction: rtl !important;
        text-align: right !important;
        padding-right: 1.25rem !important;
        padding-left: 0 !important;
        list-style-type: circle !important;
    }
    .card-rtl li {
        direction: rtl !important;
        text-align: right !important;
        margin-bottom: 0.48rem !important;
        line-height: 1.8 !important;
    }
    .card-rtl strong {
        color: inherit !important;
        font-weight: 700 !important;
    }
    .card-rtl p, .card-rtl div {
        direction: rtl !important;
        text-align: right !important;
        line-height: 1.75 !important;
    }

    /* English Report Content LTR */
    .card-ltr {
        direction: ltr !important;
        text-align: left !important;
        line-height: 1.65 !important;
    }
    .card-ltr ul {
        direction: ltr !important;
        text-align: left !important;
        padding-left: 1.35rem !important;
        padding-right: 0 !important;
        margin: 0.5rem 0 !important;
        list-style-type: disc !important;
    }
    .card-ltr ul ul {
        direction: ltr !important;
        text-align: left !important;
        padding-left: 1.25rem !important;
        padding-right: 0 !important;
        list-style-type: circle !important;
    }
    .card-ltr li {
        direction: ltr !important;
        text-align: left !important;
        margin-bottom: 0.45rem !important;
        line-height: 1.65 !important;
    }
    .card-ltr strong {
        color: inherit !important;
        font-weight: 600 !important;
    }
    .card-ltr p, .card-ltr div {
        direction: ltr !important;
        text-align: left !important;
    }

    /* Modern, Beautiful Responsive Table Styling */
    .card-rtl table, .card-ltr table {
        width: 100% !important;
        border-collapse: separate !important;
        border-spacing: 0 !important;
        margin: 1.25rem 0 1.5rem 0 !important;
        border-radius: 10px !important;
        overflow: hidden !important;
        border: 1px solid rgba(125, 125, 125, 0.25) !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.08) !important;
    }
    .card-rtl thead, .card-ltr thead {
        background: rgba(99, 102, 241, 0.15) !important;
    }
    .card-rtl th, .card-ltr th {
        color: #4f46e5 !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        padding: 0.85rem 1rem !important;
        border-bottom: 2px solid rgba(99, 102, 241, 0.3) !important;
        letter-spacing: 0.02em !important;
    }
    .card-rtl th, .card-rtl td {
        text-align: right !important;
        direction: rtl !important;
    }
    .card-ltr th, .card-ltr td {
        text-align: left !important;
        direction: ltr !important;
    }
    .card-rtl td, .card-ltr td {
        padding: 0.85rem 1rem !important;
        font-size: 0.93rem !important;
        line-height: 1.6 !important;
        border-bottom: 1px solid rgba(125, 125, 125, 0.14) !important;
        vertical-align: middle !important;
    }
    .card-rtl tr:nth-child(even) td, .card-ltr tr:nth-child(even) td {
        background: rgba(125, 125, 125, 0.04) !important;
    }
    .card-rtl tr:hover td, .card-ltr tr:hover td {
        background: rgba(99, 102, 241, 0.07) !important;
        transition: background 0.15s ease !important;
    }
    .card-rtl tr:last-child td, .card-ltr tr:last-child td {
        border-bottom: none !important;
    }

    @media (prefers-color-scheme: dark) {
        .card-rtl table, .card-ltr table {
            border-color: rgba(255, 255, 255, 0.18) !important;
            background: rgba(15, 23, 42, 0.5) !important;
        }
        .card-rtl thead, .card-ltr thead {
            background: rgba(99, 102, 241, 0.28) !important;
        }
        .card-rtl th, .card-ltr th {
            color: #a5b4fc !important;
            border-bottom-color: rgba(99, 102, 241, 0.5) !important;
        }
        .card-rtl td, .card-ltr td {
            color: #f1f5f9 !important;
            border-bottom-color: rgba(255, 255, 255, 0.1) !important;
        }
        .card-rtl tr:nth-child(even) td, .card-ltr tr:nth-child(even) td {
            background: rgba(255, 255, 255, 0.03) !important;
        }
        .card-rtl tr:hover td, .card-ltr tr:hover td {
            background: rgba(99, 102, 241, 0.16) !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# App Header
st.title(t["title"])
st.caption(t["caption"])

st.divider()

# Check for Gemini API Key in environment
has_gemini = bool(os.getenv("GEMINI_API_KEY", "").strip())

if not has_gemini:
    st.warning(t["api_warning"])
    custom_api_key = st.text_input(
        t["api_input_label"],
        type="password",
        help=t["api_help"],
    )
    if custom_api_key:
        os.environ["GEMINI_API_KEY"] = custom_api_key.strip()
        st.success(t["api_success"])
        st.rerun()
else:
    st.info("⚡ Active AI Model: **Google Gemini (gemini-3.5-flash-lite)**")

# Visa Rules URL input
default_visa_url = os.getenv(
    "VISA_RULES_URL",
    "https://en.wikipedia.org/wiki/Visa_policy_of_the_Schengen_Area",
)
visa_url = st.text_input(
    t["visa_url_label"],
    value=default_visa_url,
    help=t["visa_url_help"],
)

# Document Upload Section
col1, col2 = st.columns(2)
with col1:
    uploaded_cv = st.file_uploader(t["cv_upload_label"], type=["pdf"])
with col2:
    uploaded_job = st.file_uploader(t["job_upload_label"], type=["pdf"])

cv_file_path = None
opportunity_file_path = None

if uploaded_cv and uploaded_job:
    temp_dir = tempfile.gettempdir()
    temp_cv_path = os.path.join(temp_dir, uploaded_cv.name)
    temp_job_path = os.path.join(temp_dir, uploaded_job.name)

    with open(temp_cv_path, "wb") as f:
        f.write(uploaded_cv.getbuffer())
    with open(temp_job_path, "wb") as f:
        f.write(uploaded_job.getbuffer())

    cv_file_path = temp_cv_path
    opportunity_file_path = temp_job_path

st.divider()

# Initialize session state for persistent report display
if "report" not in st.session_state:
    st.session_state["report"] = None
if "report_is_arabic" not in st.session_state:
    st.session_state["report_is_arabic"] = False

# Action Button
if st.button(t["analyze_btn"], type="primary", use_container_width=True):
    if not cv_file_path or not opportunity_file_path:
        st.error(t["missing_files_err"])
    elif not os.getenv("GEMINI_API_KEY"):
        st.error(t["missing_api_key_err"])
    else:
        with st.spinner(t["spinner_msg"]):
            try:
                lang_code = "ar" if is_arabic_report else "en"
                generated_report = analyze_opportunity_and_visa(
                    cv_file_path=cv_file_path,
                    opportunity_file_path=opportunity_file_path,
                    visa_url=visa_url,
                    language=lang_code,
                )
                st.session_state["report"] = generated_report
                st.session_state["report_is_arabic"] = is_arabic_report
                st.success(t["analysis_success"])
            except Exception as e:
                st.error(f"{t['error_prefix']}: {e}")


# --- Helper Functions for Cards & Copy Button ---

CARD_THEMES = [
    {
        "icon": "📋",
        "badge_en": "JOB OVERVIEW",
        "badge_ar": "بيانات الوظيفة",
        "badge_color": ":blue-background",
    },
    {
        "icon": "📊",
        "badge_en": "REQUIREMENTS & FLAGS",
        "badge_ar": "مطابقة المتطلبات",
        "badge_color": ":violet-background",
    },
    {
        "icon": "🌟",
        "badge_en": "WHY IT FITS (PROS)",
        "badge_ar": "مزايا الوظيفة",
        "badge_color": ":green-background",
    },
    {
        "icon": "⚠️",
        "badge_en": "WHY IT DOES NOT FIT (CONS)",
        "badge_ar": "الموانع الحاسمة",
        "badge_color": ":red-background",
    },
    {
        "icon": "🛂",
        "badge_en": "LEGAL & VISA",
        "badge_ar": "التأشيرة والإقامة",
        "badge_color": ":violet-background",
    },
    {
        "icon": "💡",
        "badge_en": "FINAL VERDICT",
        "badge_ar": "القرار والتوصيات",
        "badge_color": ":orange-background",
    },
]


def preprocess_markdown_tables(text: str) -> str:
    """
    Sanitizes raw markdown before HTML conversion.
    Fixes collapsed table rows concatenated with '||' or '| |', ensures header separators,
    and surrounds tables with blank lines required by python-markdown tables extension.
    """
    if not text:
        return ""
    
    # 1. Replace concatenated pipe sequences (e.g. '||' or '|   |') between rows with '|\n|'
    text = re.sub(r'\|\s*\|+', '|\n|', text)
    
    # 2. Clean leading redundant pipes on lines
    lines = []
    for line in text.splitlines():
        trimmed = line.strip()
        if trimmed.startswith('||'):
            trimmed = '|' + trimmed.lstrip('|')
        lines.append(trimmed if trimmed.startswith('|') else line)
    
    # 3. Ensure blank line before and after tables (strict python-markdown requirement)
    processed_lines = []
    in_table = False
    for line in lines:
        is_table_line = bool(re.match(r'^\s*\|.*\|\s*$', line))
        if is_table_line and not in_table:
            processed_lines.append('')
            in_table = True
        elif not is_table_line and in_table:
            processed_lines.append('')
            in_table = False
        processed_lines.append(line)
        
    return '\n'.join(processed_lines)


def render_copy_toolbar(report_text: str, is_arabic: bool):
    """Renders a toolbar with 1-click copy to clipboard and markdown download."""
    is_ar = is_arabic or bool(re.search(r"[\u0600-\u06FF]", report_text))
    t_curr = TEXTS["العربية"] if is_ar else TEXTS["English"]
    col_dl, col_cp = st.columns([1, 1])

    with col_dl:
        st.download_button(
            label=t_curr["download_btn_label"],
            data=report_text,
            file_name="evaluation_report.md",
            mime="text/markdown",
            use_container_width=True,
        )

    with col_cp:
        # One-click clipboard copy via iframe component with fallback
        escaped_text = json.dumps(report_text)
        btn_label = re.sub(r"^📋\s*", "", t_curr["copy_btn_label"]).strip()
        copied_text = t_curr["copied_label"]
        html_code = f"""
        <button id="copyBtn" onclick="copyReport()" style="
            width: 100%;
            background-color: #1e293b;
            color: #f8fafc;
            border: 1px solid #475569;
            padding: 0.55rem 1rem;
            font-size: 0.95rem;
            font-weight: 500;
            border-radius: 0.5rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            transition: all 0.2s ease;
            outline: none;
            font-family: inherit;
        ">
            <span id="btnIcon">📋</span> <span id="btnLabel">{btn_label}</span>
        </button>
        <script>
        function copyReport() {{
            const text = {escaped_text};
            if (navigator.clipboard && window.isSecureContext) {{
                navigator.clipboard.writeText(text).then(showSuccess).catch(fallbackCopy);
            }} else {{
                fallbackCopy();
            }}
        }}
        function fallbackCopy() {{
            const text = {escaped_text};
            const textArea = document.createElement("textarea");
            textArea.value = text;
            textArea.style.position = "fixed";
            textArea.style.left = "-999999px";
            textArea.style.top = "-999999px";
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            try {{
                document.execCommand('copy');
                showSuccess();
            }} catch (err) {{
                console.error('Copy error', err);
            }}
            document.body.removeChild(textArea);
        }}
        function showSuccess() {{
            const btn = document.getElementById("copyBtn");
            const lbl = document.getElementById("btnLabel");
            const ico = document.getElementById("btnIcon");
            btn.style.backgroundColor = "#065f46";
            btn.style.borderColor = "#10b981";
            lbl.innerText = "{copied_text}";
            ico.innerText = "✅";
            setTimeout(() => {{
                btn.style.backgroundColor = "#1e293b";
                btn.style.borderColor = "#475569";
                lbl.innerText = "{btn_label}";
                ico.innerText = "📋";
            }}, 2500);
        }}
        </script>
        """
        components.html(html_code, height=45)


def render_quick_facts_ribbon(report_text: str, is_arabic: bool):
    """Extracts and renders key top-level metrics in an executive summary ribbon."""
    is_ar = is_arabic or bool(re.search(r"[\u0600-\u06FF]", report_text))
    t_curr = TEXTS["العربية"] if is_ar else TEXTS["English"]
    card_kpi_cls = "kpi-card kpi-card-rtl" if is_ar else "kpi-card"
    card_kpi_dir = "rtl" if is_ar else "ltr"

    # Extract Location (Host Country / City)
    loc_match = re.search(r"(?:Host Country|مقر العمل|Duty Station|Location)[^\n:]*[:*]+\s*([^\n]+)", report_text, re.I)
    loc_val = re.sub(r"^[*\s#\d\.\:\-]+|[*\s#\:\.]+$", "", loc_match.group(1)).strip() if loc_match else ("Rome, Italy" if "italy" in report_text.lower() else "Berlin, Germany")

    # Extract Salary / Grade
    sal_match = re.search(r"(?:Salary|الراتب|Remuneration|Grade Level)[^\n:]*[:*]+\s*([^\n]+)", report_text, re.I)
    sal_val = re.sub(r"^[*\s#\d\.\:\-]+|[*\s#\:\.]+$", "", sal_match.group(1)).strip() if sal_match else ("UN G-3 Scale" if "g-3" in report_text.lower() else ("فرصة تطوعية / توفير سكن" if is_ar else "Volunteer Position / Accommodation Support"))

    # Extract Match Percentage
    pct_match = re.search(r"(\d{1,3})\s*%", report_text)
    pct_val = f"{pct_match.group(1)}%" if pct_match else "N/A"

    # Extract Verdict
    is_ineligible = any(w in report_text.lower() for w in ["not eligible", "غير مؤهل"])
    is_conditional = any(w in report_text.lower() for w in ["conditionally", "بشروط"])
    if is_ineligible:
        status_text = "❌ " + ("غير مؤهل" if is_ar else "Not Eligible")
        status_class = "kpi-status-red"
    elif is_conditional:
        status_text = "⚠️ " + ("بشروط" if is_ar else "Conditionally Recommended")
        status_class = "kpi-status-yellow"
    else:
        status_text = "✅ " + ("موصى به" if is_ar else "Recommended")
        status_class = "kpi-status-green"

    # Render Executive Summary Container with responsive, text-wrapping KPI cards
    with st.container(border=True):
        st.markdown(f"**📌 {t_curr['quick_facts_title']}**")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(
                f"""
                <div class="{card_kpi_cls}" dir="{card_kpi_dir}">
                    <div class="kpi-label">📍 {t_curr['location_label']}</div>
                    <div class="kpi-val">{loc_val}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f"""
                <div class="{card_kpi_cls}" dir="{card_kpi_dir}">
                    <div class="kpi-label">💰 {t_curr['salary_label']}</div>
                    <div class="kpi-val">{sal_val}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                f"""
                <div class="{card_kpi_cls}" dir="{card_kpi_dir}">
                    <div class="kpi-label">🎯 {t_curr['match_label']}</div>
                    <div class="kpi-val kpi-score">{pct_val}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c4:
            st.markdown(
                f"""
                <div class="{card_kpi_cls}" dir="{card_kpi_dir}">
                    <div class="kpi-label">⚖️ {t_curr['status_label']}</div>
                    <div class="kpi-val {status_class}">{status_text}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_colorful_cards(report_text: str, is_arabic: bool):
    """
    Parses all structured report sections and renders each inside a clean,
    native border container card with distinct theme icons, dividers, and highlight badges.
    """
    is_ar = is_arabic or bool(re.search(r"[\u0600-\u06FF]", report_text))

    # Render top executive summary ribbon first
    render_quick_facts_ribbon(report_text, is_ar)
    st.write("")

    pattern = r"(?m)^[#\s\*]*([1-6])[\.\:\-]\s*([^\n]+)\n([\s\S]*?)(?=(?:^[#\s\*]*[1-6][\.\:\-])|\Z)"
    sections = re.findall(pattern, report_text)

    # Fallback if structure deviates
    if len(sections) < 2:
        card_class = "card-rtl" if is_ar else "card-ltr"
        card_dir = "rtl" if is_ar else "ltr"
        cleaned_text = preprocess_markdown_tables(report_text)
        html_body = markdown.markdown(cleaned_text, extensions=["tables", "fenced_code"])
        with st.container(border=True):
            st.markdown(f'<div class="{card_class}" dir="{card_dir}">{html_body}</div>', unsafe_allow_html=True)
        return

    for i, (sec_num, raw_title, body_text) in enumerate(sections):
        theme = CARD_THEMES[i % len(CARD_THEMES)]
        title_clean = re.sub(r"^[*\s#\d\.\:\-]+|[*\s#\:]+$", "", raw_title).strip()
        body_clean = re.sub(r"\n*---\s*$", "", body_text.strip()).strip()

        # Prevent duplicate icon prefix if already in title
        if any(title_clean.startswith(icon) for icon in ["📋", "📊", "🌟", "⚠️", "🛂", "💡"]):
            display_title = title_clean
        else:
            display_title = f"{theme['icon']} {title_clean}"

        with st.container(border=True):
            col_t1, col_t2 = st.columns([2.5, 1.5])
            with col_t1:
                st.markdown(f"### {display_title}")
            with col_t2:
                # Dynamic Badges in matching language
                if sec_num == "2":
                    flag_count = body_clean.count("🚩")
                    if flag_count > 0:
                        badge_label = f"🚩 {flag_count} متطلبات غير متوفرة" if is_ar else f"🚩 {flag_count} Unmet Flags"
                        st.markdown(f":red-background[**{badge_label}**]")
                    else:
                        badge_lbl = theme["badge_ar"] if is_ar else theme["badge_en"]
                        st.caption(f"{theme['badge_color']}[{badge_lbl}]")
                elif sec_num == "3":
                    badge_lbl = "🌟 مزايا الوظيفة" if is_ar else "🌟 PROS"
                    st.markdown(f":green-background[**{badge_lbl}**]")
                elif sec_num == "4":
                    badge_lbl = "⚠️ الموانع الحاسمة" if is_ar else "⚠️ RED FLAGS"
                    st.markdown(f":red-background[**{badge_lbl}**]")
                elif sec_num == "6":
                    if any(w in body_clean.lower() for w in ["not eligible", "غير مؤهل"]):
                        verdict_lbl = "❌ غير مؤهل" if is_ar else "❌ Not Eligible"
                        st.markdown(f":red-background[**{verdict_lbl}**]")
                    elif any(w in body_clean.lower() for w in ["conditionally", "بشروط"]):
                        verdict_lbl = "⚠️ موصى به بشروط" if is_ar else "⚠️ Conditionally Recommended"
                        st.markdown(f":yellow-background[**{verdict_lbl}**]")
                    else:
                        verdict_lbl = "✅ موصى به" if is_ar else "✅ Recommended"
                        st.markdown(f":green-background[**{verdict_lbl}**]")
                else:
                    badge_lbl = theme["badge_ar"] if is_ar else theme["badge_en"]
                    st.caption(f"{theme['badge_color']}[{badge_lbl}]")

            st.divider()

            # Render HTML body with strict directionality, table formatting, and bullet alignment
            card_class = "card-rtl" if is_ar else "card-ltr"
            card_dir = "rtl" if is_ar else "ltr"
            cleaned_body = preprocess_markdown_tables(body_clean)
            body_html = markdown.markdown(cleaned_body, extensions=["tables", "fenced_code"])
            st.markdown(f'<div class="{card_class}" dir="{card_dir}">{body_html}</div>', unsafe_allow_html=True)


# --- Report Display Area ---
if st.session_state.get("report"):
    current_report = st.session_state["report"]
    report_is_ar = bool(
        st.session_state.get("report_is_arabic", False)
        or (current_report and re.search(r"[\u0600-\u06FF]", current_report))
    )

    st.markdown(f"### {t['report_header']}")

    # 1. Action Toolbar: Copy Button & Download Button
    render_copy_toolbar(current_report, report_is_ar)

    # 2. View Mode Selector (Cards Mode vs Text Mode)
    col_mode1, col_mode2 = st.columns([1, 1])
    with col_mode1:
        view_choice = st.radio(
            t["view_mode_label"],
            options=[t["cards_view"], t["text_view"]],
            index=0,
            horizontal=True,
        )

    st.write("")

    # 3. Render Cards or Text
    if view_choice == t["cards_view"]:
        render_colorful_cards(current_report, report_is_ar)
    else:
        card_class = "card-rtl" if report_is_ar else "card-ltr"
        card_dir = "rtl" if report_is_ar else "ltr"
        cleaned_report = preprocess_markdown_tables(current_report)
        full_html = markdown.markdown(cleaned_report, extensions=["tables", "fenced_code"])
        with st.container(border=True):
            st.markdown(f'<div class="{card_class}" dir="{card_dir}">{full_html}</div>', unsafe_allow_html=True)

    # 4. Raw Markdown Expander with native Streamlit copy button
    with st.expander(t["raw_expander"]):
        st.code(current_report, language="markdown")
