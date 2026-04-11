"""
AI Resume Generator — Main Streamlit Application.
Professional SaaS dashboard for resume optimization, generation, and career tracking.
"""

import streamlit as st
from datetime import datetime

from resume_parser import parse_resume, ResumeParseError
from resume_generator import generate_resume_from_scratch
from optimizer import optimize_resume
from cover_letter import generate_cover_letter
from skill_matcher import calculate_match_score
from storage import (
    save_resume, load_resumes, save_application, load_applications,
    update_application_status, delete_application,
)
from config import APPLICATION_STATUSES
from llm_helper import LLMError, check_ollama_connection
from pdf_generator import generate_pdf, get_pdf_preview_html, AVAILABLE_TEMPLATES
from suggestions import generate_suggestions
from logger import get_logger

logger = get_logger(__name__)


# ════════════════════════════════════════════════════════════════════════════════
#  PAGE CONFIG
# ════════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="AI Resume Generator",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ════════════════════════════════════════════════════════════════════════════════
#  PREMIUM LIGHT THEME CSS
# ════════════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
/* ─── Google Font ─── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ─── Hide Streamlit defaults ─── */
#MainMenu, footer, header { visibility: hidden; }

/* ─── Root variables ─── */
:root {
    --primary: #0A66C2;
    --primary-light: #E8F1FB;
    --primary-hover: #004182;
    --bg: #F3F2EF;
    --card-bg: #FFFFFF;
    --text-primary: #191919;
    --text-secondary: #666666;
    --text-muted: #8C8C8C;
    --border: #E0E0E0;
    --success: #057642;
    --success-bg: #E8F5E9;
    --warning: #915B00;
    --warning-bg: #FFF8E1;
    --danger: #CC1016;
    --danger-bg: #FFEBEE;
    --radius: 10px;
    --shadow: 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06);
    --shadow-md: 0 4px 12px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.06);
}

/* ══════════════════════════════════════════════════════════════
   FORCE LIGHT MODE — override every Streamlit dark-mode style
   ══════════════════════════════════════════════════════════════ */

/* ─── Global body + all text ─── */
html, body, [class*="css"],
.stMarkdown, .stMarkdown p, .stMarkdown li,
.stMarkdown span, .stMarkdown div,
.stText {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    color: #191919 !important;
}

/* Subtitle text on pages */
.page-subtitle {
    color: #666666 !important;
    font-size: 0.95rem !important;
    margin-top: -8px !important;
    margin-bottom: 24px !important;
    line-height: 1.5 !important;
}

.stApp {
    background-color: #F3F2EF !important;
}

/* ─── Sidebar — force white ─── */
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div,
section[data-testid="stSidebar"] > div > div,
section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    background: #FFFFFF !important;
    background-color: #FFFFFF !important;
    color: #191919 !important;
    border-right: 1px solid #E0E0E0 !important;
}

section[data-testid="stSidebar"] * {
    color: #191919 !important;
}

section[data-testid="stSidebar"] .stMarkdown h1 {
    color: #0A66C2 !important;
    font-size: 1.35rem !important;
    font-weight: 700 !important;
}

section[data-testid="stSidebar"] .stRadio > label {
    display: none !important;
}

section[data-testid="stSidebar"] .stRadio > div {
    gap: 2px !important;
}

section[data-testid="stSidebar"] .stRadio > div > label {
    background: transparent !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 16px !important;
    margin: 0 !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    color: #666666 !important;
    transition: all 0.2s ease !important;
    cursor: pointer !important;
}

/* HIDE the radio button dot/circle indicator — exact Streamlit selector */
[data-testid="stRadioSelectionIndicator"] {
    display: none !important;
    width: 0 !important;
    height: 0 !important;
    overflow: hidden !important;
}

/* Fallback: hide radio input and any indicator divs */
div[role="radiogroup"] input[type="radio"] {
    display: none !important;
}

/* Hide pseudo-elements that might render dots */
div[role="radiogroup"] label div::before,
div[role="radiogroup"] label div::after {
    content: none !important;
    display: none !important;
}

/* Hide any SVG radio indicators */
section[data-testid="stSidebar"] .stRadio svg {
    display: none !important;
    width: 0 !important;
    height: 0 !important;
}

section[data-testid="stSidebar"] .stRadio > div > label p {
    color: #666666 !important;
}

section[data-testid="stSidebar"] .stRadio > div > label:hover {
    background: #E8F1FB !important;
    color: #0A66C2 !important;
}
section[data-testid="stSidebar"] .stRadio > div > label:hover p {
    color: #0A66C2 !important;
}

section[data-testid="stSidebar"] .stRadio > div > label[data-checked="true"],
section[data-testid="stSidebar"] .stRadio > div > label[aria-checked="true"] {
    background: #E8F1FB !important;
}
section[data-testid="stSidebar"] .stRadio > div > label[data-checked="true"] p,
section[data-testid="stSidebar"] .stRadio > div > label[aria-checked="true"] p {
    color: #0A66C2 !important;
    font-weight: 600 !important;
}

/* Sidebar dividers */
section[data-testid="stSidebar"] hr {
    border-color: #E0E0E0 !important;
}

/* ─── Main content area ─── */
.block-container {
    padding: 2rem 3rem 3rem 3rem !important;
    max-width: 1200px !important;
}

/* ─── ALL text elements — nuclear override ─── */
h1 {
    color: #191919 !important;
    font-weight: 700 !important;
    font-size: 1.75rem !important;
    letter-spacing: -0.5px !important;
    margin-bottom: 0.25rem !important;
}

h2, .stSubheader {
    color: #191919 !important;
    font-weight: 600 !important;
    font-size: 1.15rem !important;
    margin-top: 1.5rem !important;
    margin-bottom: 0.75rem !important;
}

h3 {
    color: #191919 !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
}

/* ─── Cards / Containers — force white bg ─── */
div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #FFFFFF !important;
    background-color: #FFFFFF !important;
    border: 1px solid #E0E0E0 !important;
    border-radius: 10px !important;
    padding: 0 !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08) !important;
    overflow: hidden !important;
    margin-bottom: 16px !important;
}

div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] > div {
    padding: 24px 28px !important;
    background: #FFFFFF !important;
}

/* ─── Buttons ─── */
.stButton > button {
    background: #0A66C2 !important;
    background-color: #0A66C2 !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 24px !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    padding: 10px 24px !important;
    transition: all 0.2s ease !important;
    box-shadow: none !important;
}

.stButton > button:hover {
    background: #004182 !important;
    background-color: #004182 !important;
    color: #FFFFFF !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.12) !important;
    transform: translateY(-1px);
}

.stButton > button:active {
    transform: translateY(0);
}

.stButton > button p,
.stButton > button span {
    color: #FFFFFF !important;
}

/* Secondary / outline buttons */
.stDownloadButton > button {
    background: #FFFFFF !important;
    background-color: #FFFFFF !important;
    color: #0A66C2 !important;
    border: 1.5px solid #0A66C2 !important;
    border-radius: 24px !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    padding: 8px 20px !important;
}

.stDownloadButton > button:hover {
    background: #E8F1FB !important;
    background-color: #E8F1FB !important;
}

.stDownloadButton > button p,
.stDownloadButton > button span {
    color: #0A66C2 !important;
}

/* ─── ALL Inputs — force light ─── */
input, textarea, select {
    background: #FFFFFF !important;
    background-color: #FFFFFF !important;
    color: #191919 !important;
    border-color: #E0E0E0 !important;
}

.stTextInput > div > div > input,
.stTextInput input {
    background: #FFFFFF !important;
    background-color: #FFFFFF !important;
    border: 1.5px solid #E0E0E0 !important;
    border-radius: 8px !important;
    padding: 10px 14px !important;
    font-size: 0.9rem !important;
    color: #191919 !important;
    caret-color: #191919 !important;
}

.stTextArea > div > div > textarea,
.stTextArea textarea {
    background: #FFFFFF !important;
    background-color: #FFFFFF !important;
    border: 1.5px solid #E0E0E0 !important;
    border-radius: 8px !important;
    padding: 10px 14px !important;
    font-size: 0.9rem !important;
    color: #191919 !important;
    caret-color: #191919 !important;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #0A66C2 !important;
    box-shadow: 0 0 0 3px rgba(10,102,194,0.12) !important;
}

.stTextInput > div > div > input::placeholder,
.stTextArea > div > div > textarea::placeholder {
    color: #A0A0A0 !important;
}

/* Input labels */
.stTextInput label, .stTextArea label,
.stSelectbox label, .stFileUploader label,
.stDateInput label, .stCheckbox label,
.stNumberInput label {
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    color: #444444 !important;
    margin-bottom: 6px !important;
}

.stTextInput label p, .stTextArea label p,
.stSelectbox label p, .stFileUploader label p,
.stDateInput label p {
    color: #444444 !important;
}

/* Make file uploader label clearly visible above dropzone */
.stFileUploader label {
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    color: #191919 !important;
    margin-bottom: 8px !important;
    display: block !important;
}

.stFileUploader label p {
    color: #191919 !important;
}

/* ─── Selectbox — force light ─── */
.stSelectbox > div > div,
.stSelectbox [data-baseweb="select"],
.stSelectbox [data-baseweb="select"] > div {
    background: #FFFFFF !important;
    background-color: #FFFFFF !important;
    border: 1.5px solid #E0E0E0 !important;
    border-radius: 8px !important;
    color: #191919 !important;
}

.stSelectbox [data-baseweb="select"] span,
.stSelectbox [data-baseweb="select"] div {
    color: #191919 !important;
}

/* Selectbox dropdown menu */
[data-baseweb="popover"],
[data-baseweb="menu"],
[data-baseweb="popover"] ul,
[data-baseweb="menu"] ul,
ul[role="listbox"] {
    background: #FFFFFF !important;
    background-color: #FFFFFF !important;
    border: 1px solid #E0E0E0 !important;
    border-radius: 8px !important;
}

[data-baseweb="menu"] li,
ul[role="listbox"] li,
[role="option"] {
    background: #FFFFFF !important;
    color: #191919 !important;
}

[data-baseweb="menu"] li:hover,
ul[role="listbox"] li:hover,
[role="option"]:hover,
[role="option"][aria-selected="true"] {
    background: #E8F1FB !important;
    background-color: #E8F1FB !important;
    color: #0A66C2 !important;
}

/* ─── Date Input — force light ─── */
.stDateInput > div > div,
.stDateInput input,
.stDateInput [data-baseweb="input"],
.stDateInput [data-baseweb="input"] > div {
    background: #FFFFFF !important;
    background-color: #FFFFFF !important;
    border: 1.5px solid #E0E0E0 !important;
    border-radius: 8px !important;
    color: #191919 !important;
}

.stDateInput input {
    color: #191919 !important;
}

/* Date picker calendar popup */
[data-baseweb="calendar"],
[data-baseweb="datepicker"],
[data-baseweb="calendar"] div,
[data-baseweb="datepicker"] div {
    background: #FFFFFF !important;
    background-color: #FFFFFF !important;
    color: #191919 !important;
}

/* ─── Checkbox — force visible text ─── */
.stCheckbox,
.stCheckbox label,
.stCheckbox span,
.stCheckbox p {
    color: #666666 !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
}

.stCheckbox [data-testid="stCheckbox"] label span {
    color: #666666 !important;
}

/* ─── File uploader — force light ─── */
.stFileUploader > div,
.stFileUploader section,
.stFileUploader [data-testid="stFileUploader"],
.stFileUploader [data-testid="stFileUploaderDropzone"] {
    background: #FAFAFA !important;
    background-color: #FAFAFA !important;
    border: 2px dashed #D0D0D0 !important;
    border-radius: 10px !important;
    padding: 24px !important;
    color: #666666 !important;
}

.stFileUploader > div:hover,
.stFileUploader [data-testid="stFileUploaderDropzone"]:hover {
    border-color: #0A66C2 !important;
    background: #E8F1FB !important;
    background-color: #E8F1FB !important;
}

.stFileUploader span,
.stFileUploader p,
.stFileUploader div,
.stFileUploader small,
.stFileUploader label {
    color: #666666 !important;
}

.stFileUploader button {
    background: #FFFFFF !important;
    color: #0A66C2 !important;
    border: 1.5px solid #0A66C2 !important;
    border-radius: 8px !important;
}

/* ─── Metrics — force white card ─── */
div[data-testid="stMetric"] {
    background: #FFFFFF !important;
    background-color: #FFFFFF !important;
    border: 1px solid #E0E0E0 !important;
    border-radius: 10px !important;
    padding: 20px 24px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08) !important;
}

div[data-testid="stMetric"] label {
    color: #8C8C8C !important;
    font-weight: 500 !important;
    font-size: 0.8rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}

div[data-testid="stMetric"] label p {
    color: #8C8C8C !important;
}

div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: #0A66C2 !important;
    font-weight: 700 !important;
    font-size: 1.75rem !important;
}

div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
    color: #057642 !important;
}

/* ─── Expander — force light ─── */
.streamlit-expanderHeader,
details > summary,
[data-testid="stExpander"] summary,
[data-testid="stExpander"] > details > summary {
    background: #FFFFFF !important;
    background-color: #FFFFFF !important;
    border: 1px solid #E0E0E0 !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    color: #191919 !important;
    padding: 14px 18px !important;
}

.streamlit-expanderContent,
details > div,
[data-testid="stExpander"] > details > div[data-testid="stExpanderDetails"] {
    background: #FFFFFF !important;
    background-color: #FFFFFF !important;
    border: 1px solid #E0E0E0 !important;
    border-top: none !important;
    border-radius: 0 0 10px 10px !important;
    padding: 18px 20px !important;
    color: #191919 !important;
}

[data-testid="stExpander"] summary span,
[data-testid="stExpander"] summary p {
    color: #191919 !important;
}

/* ─── Code blocks — FORCE LIGHT background ─── */
.stCodeBlock,
.stCodeBlock > div,
.stCodeBlock pre,
.stCodeBlock code,
[data-testid="stCodeBlock"],
[data-testid="stCodeBlock"] > div,
[data-testid="stCodeBlock"] pre,
[data-testid="stCodeBlock"] code,
pre, code {
    background: #F8F9FA !important;
    background-color: #F8F9FA !important;
    color: #191919 !important;
    border: 1px solid #E0E0E0 !important;
    border-radius: 10px !important;
}

.stCodeBlock pre code,
[data-testid="stCodeBlock"] pre code {
    border: none !important;
}

/* Code copy button */
.stCodeBlock button,
[data-testid="stCodeBlock"] button {
    background: #FFFFFF !important;
    border: 1px solid #E0E0E0 !important;
    color: #666666 !important;
}

/* ─── Alerts / info / warning / error — force light ─── */
.stAlert,
[data-testid="stAlert"],
.stAlert > div,
[data-baseweb="notification"] {
    border-radius: 10px !important;
    font-size: 0.85rem !important;
    padding: 14px 18px !important;
    border: none !important;
}

/* Info alert */
[data-testid="stAlert"][data-type="info"],
div[role="alert"]:not([data-type]) {
    background: #E8F1FB !important;
    background-color: #E8F1FB !important;
    color: #0A66C2 !important;
}

div[role="alert"] p,
[data-testid="stAlert"] p,
.stAlert p {
    color: inherit !important;
}

/* Success alert */
[data-testid="stAlert"][data-type="success"],
.stSuccess {
    background: #E8F5E9 !important;
    background-color: #E8F5E9 !important;
    color: #057642 !important;
}

/* Warning alert */
[data-testid="stAlert"][data-type="warning"] {
    background: #FFF8E1 !important;
    background-color: #FFF8E1 !important;
    color: #915B00 !important;
}

/* Error alert */
[data-testid="stAlert"][data-type="error"] {
    background: #FFEBEE !important;
    background-color: #FFEBEE !important;
    color: #CC1016 !important;
}

/* ─── Progress bar ─── */
.stProgress > div > div > div {
    background: #0A66C2 !important;
    border-radius: 8px !important;
}

.stProgress > div > div {
    background: #E0E0E0 !important;
}

/* ─── Dividers ─── */
hr {
    border: none !important;
    border-top: 1px solid #E0E0E0 !important;
    margin: 24px 0 !important;
}

/* ─── Forms — force white ─── */
[data-testid="stForm"],
[data-testid="stForm"] > div {
    background: #FFFFFF !important;
    background-color: #FFFFFF !important;
    border: 1px solid #E0E0E0 !important;
    border-radius: 10px !important;
    padding: 28px 32px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08) !important;
    color: #191919 !important;
}

/* Form submit button */
[data-testid="stForm"] .stButton > button,
.stFormSubmitButton > button {
    background: #0A66C2 !important;
    color: #FFFFFF !important;
}

[data-testid="stForm"] .stButton > button p,
.stFormSubmitButton > button p {
    color: #FFFFFF !important;
}

/* ─── Caption ─── */
.stCaption, [data-testid="stCaptionContainer"],
.stCaption p, [data-testid="stCaptionContainer"] p {
    color: #8C8C8C !important;
    font-size: 0.8rem !important;
}

/* ─── Markdown text ─── */
.stMarkdown p {
    color: #191919 !important;
}

.stMarkdown strong, .stMarkdown b {
    color: #191919 !important;
}

.stMarkdown a {
    color: #0A66C2 !important;
}

/* ─── Spinner ─── */
.stSpinner > div > div {
    border-top-color: #0A66C2 !important;
}

/* ─── Scrollbar ─── */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}
::-webkit-scrollbar-track {
    background: #F3F2EF;
}
::-webkit-scrollbar-thumb {
    background: #C4C4C4;
    border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
    background: #A0A0A0;
}

/* ─── Tooltip / popover ─── */
[data-baseweb="tooltip"],
[data-baseweb="popover"] > div {
    background: #FFFFFF !important;
    color: #191919 !important;
    border: 1px solid #E0E0E0 !important;
}

/* ═══════════════════════════════════════════
   CUSTOM COMPONENTS
   ═══════════════════════════════════════════ */

/* ─── Hero banner ─── */
.hero-banner {
    background: linear-gradient(135deg, #0A66C2 0%, #004182 100%);
    border-radius: 14px;
    padding: 48px 40px;
    margin-bottom: 32px;
    color: #FFFFFF;
    position: relative;
    overflow: hidden;
}
.hero-banner::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -20%;
    width: 400px;
    height: 400px;
    background: rgba(255,255,255,0.06);
    border-radius: 50%;
}
.hero-banner::after {
    content: '';
    position: absolute;
    bottom: -30%;
    left: -10%;
    width: 300px;
    height: 300px;
    background: rgba(255,255,255,0.04);
    border-radius: 50%;
}
.hero-banner h1 {
    color: #FFFFFF !important;
    font-size: 2rem !important;
    font-weight: 800 !important;
    margin-bottom: 8px !important;
    position: relative;
    z-index: 1;
}
.hero-banner p {
    color: rgba(255,255,255,0.85) !important;
    font-size: 1.05rem;
    font-weight: 400;
    margin: 0;
    position: relative;
    z-index: 1;
    line-height: 1.6;
}

/* ─── Feature cards ─── */
.feature-card {
    background: #FFFFFF;
    border: 1px solid #E0E0E0;
    border-radius: 10px;
    padding: 28px 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    transition: all 0.25s ease;
    height: 100%;
}
.feature-card:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    transform: translateY(-2px);
    border-color: #0A66C2;
}
.feature-card .card-icon {
    width: 48px;
    height: 48px;
    background: #E8F1FB;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.4rem;
    margin-bottom: 16px;
}
.feature-card h3 {
    font-size: 1.05rem !important;
    font-weight: 700 !important;
    color: #191919 !important;
    margin-bottom: 8px !important;
}
.feature-card p {
    font-size: 0.88rem;
    color: #666666 !important;
    line-height: 1.6;
    margin-bottom: 12px;
}
.feature-card ul {
    list-style: none;
    padding: 0;
    margin: 0;
}
.feature-card ul li {
    font-size: 0.84rem;
    color: #666666 !important;
    padding: 4px 0;
    display: flex;
    align-items: center;
    gap: 8px;
}
.feature-card ul li::before {
    content: '✓';
    color: #0A66C2;
    font-weight: 700;
    font-size: 0.85rem;
}

/* ─── Section header with accent ─── */
.section-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 20px;
    margin-top: 8px;
}
.section-header .icon-box {
    width: 40px;
    height: 40px;
    background: #E8F1FB;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.15rem;
    flex-shrink: 0;
}
.section-header h2 {
    font-size: 1.15rem !important;
    font-weight: 700 !important;
    color: #191919 !important;
    margin: 0 !important;
    padding: 0 !important;
}
.section-header p {
    font-size: 0.82rem;
    color: #8C8C8C !important;
    margin: 2px 0 0 0;
}

/* ─── Skill pill badges ─── */
.skill-pill {
    display: inline-block;
    background: #E8F1FB;
    color: #0A66C2 !important;
    padding: 5px 14px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
    margin: 3px 4px;
    border: 1px solid rgba(10,102,194,0.15);
}
.skill-pill.missing {
    background: #FFF3E0;
    color: #E65100 !important;
    border-color: rgba(230,81,0,0.15);
}

/* ─── Status badges ─── */
.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 14px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
}
.status-applied { background: #E8F1FB; color: #0A66C2 !important; }
.status-interview { background: #E8F5E9; color: #2E7D32 !important; }
.status-review { background: #FFF8E1; color: #F57F17 !important; }
.status-rejected { background: #FFEBEE; color: #C62828 !important; }
.status-offer { background: #E8F5E9; color: #1B5E20 !important; }
.status-accepted { background: #E0F2F1; color: #00695C !important; }
.status-withdrawn { background: #F5F5F5; color: #757575 !important; }

/* ─── Ollama status badge ─── */
.status-online {
    background: #E8F5E9;
    color: #057642 !important;
    padding: 8px 16px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.82rem;
    display: flex;
    align-items: center;
    gap: 8px;
}
.status-offline {
    background: #FFEBEE;
    color: #CC1016 !important;
    padding: 8px 16px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.82rem;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* ─── Footer ─── */
.custom-footer {
    text-align: center;
    padding: 24px 0 8px 0;
    color: #8C8C8C !important;
    font-size: 0.8rem;
    letter-spacing: 0.2px;
}

.custom-footer strong {
    color: #666666 !important;
}

/* ─── Spacing & overlap fixes ─── */
div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stVerticalBlock"] {
    gap: 12px !important;
}

div[data-testid="column"] {
    padding: 0 6px !important;
}

/* ─── Prevent tight overlap on all pages ─── */
.stMarkdown {
    margin-bottom: 4px !important;
}

.element-container {
    margin-bottom: 8px !important;
}

</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
#  SESSION STATE
# ════════════════════════════════════════════════════════════════════════════════

_DEFAULTS = {
    "optimized_resume": None,
    "generated_resume": None,
    "cover_letter": None,
    "match_result": None,
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# Initialize nav selection in session state
if "nav_selection" not in st.session_state:
    st.session_state.nav_selection = "🏠 Home"

_api_ok = check_ollama_connection()


# ════════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ════════════════════════════════════════════════════════════════════════════════

def _show_resume(text: str):
    """Render resume text in a scrollable code block."""
    st.code(text, language=None)


def _on_nav_change():
    """Reset transient results when switching pages."""
    for key in ["optimized_resume", "generated_resume", "cover_letter", "match_result"]:
        st.session_state[key] = None


STATUS_COLORS = {
    "Applied": "🔵",
    "Interview Scheduled": "🟢",
    "Under Review": "🟡",
    "Rejected": "🔴",
    "Offer Received": "🟢",
    "Accepted": "✅",
    "Withdrawn": "⚪",
}

STATUS_CSS_CLASS = {
    "Applied": "status-applied",
    "Interview Scheduled": "status-interview",
    "Under Review": "status-review",
    "Rejected": "status-rejected",
    "Offer Received": "status-offer",
    "Accepted": "status-accepted",
    "Withdrawn": "status-withdrawn",
}


def _section_header(icon: str, title: str, subtitle: str = ""):
    """Render a styled section header with icon box."""
    sub_html = f"<p>{subtitle}</p>" if subtitle else ""
    st.markdown(f"""
    <div class="section-header">
        <div class="icon-box">{icon}</div>
        <div>
            <h2>{title}</h2>
            {sub_html}
        </div>
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ════════════════════════════════════════════════════════════════════════════════

_NAV_OPTIONS = [
    "🏠 Home",
    "🔧 Optimize Resume",
    "📝 Build from Scratch",
    "📊 Application Tracker",
    "📁 Resume History",
]

_NAV_MAP = {
    "🏠 Home": "home",
    "🔧 Optimize Resume": "optimize",
    "📝 Build from Scratch": "build",
    "📊 Application Tracker": "tracker",
    "📁 Resume History": "history",
}

with st.sidebar:
    st.markdown("""
    <div style="padding: 16px 4px 8px 4px;">
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 4px;">
            <div style="width: 36px; height: 36px; background: linear-gradient(135deg, #0A66C2, #004182); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 1.1rem; color: white;">📄</div>
            <div>
                <div style="font-size: 1.1rem; font-weight: 700; color: #191919; letter-spacing: -0.3px;">Resume Generator</div>
                <div style="font-size: 0.72rem; color: #8C8C8C; font-weight: 500;">AI-Powered Career Tools · v2.0</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # System status
    if _api_ok:
        st.markdown('<div class="status-online">🟢 Ollama Connected</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-offline">🔴 Ollama Offline</div>', unsafe_allow_html=True)
        st.caption("Run `ollama serve` to start.")

    st.divider()

    st.radio(
        "Navigation",
        _NAV_OPTIONS,
        key="nav_selection",
        on_change=_on_nav_change,
        label_visibility="collapsed",
    )

    st.divider()
    st.markdown("""
    <div style="text-align: center; padding: 8px 0; color: #8C8C8C; font-size: 0.72rem;">
        Powered by <strong>Ollama</strong> · Built with <strong>Streamlit</strong>
    </div>
    """, unsafe_allow_html=True)

page = _NAV_MAP[st.session_state.nav_selection]


# ════════════════════════════════════════════════════════════════════════════════
#  HOME
# ════════════════════════════════════════════════════════════════════════════════

if page == "home":
    # Hero banner
    st.markdown("""
    <div class="hero-banner">
        <h1>Welcome to AI Resume Generator</h1>
        <p>
            Intelligent resume analysis, optimization, and career assistance — powered by local AI.<br>
            Build professional, ATS-optimized resumes and track your job applications in one place.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Feature cards
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown("""
        <div class="feature-card">
            <div class="card-icon">🔧</div>
            <h3>Optimize Existing Resume</h3>
            <p>Upload your resume and a job description. AI will analyze, optimize, and tailor it for ATS compatibility.</p>
            <ul>
                <li>Skill gap analysis with visual charts</li>
                <li>ATS-friendly bullet point rewriting</li>
                <li>Job-specific keyword optimization</li>
                <li>Optional AI cover letter generation</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="feature-card">
            <div class="card-icon">📝</div>
            <h3>Build Resume from Scratch</h3>
            <p>No resume? Fill in guided fields and AI will generate a complete professional resume for you.</p>
            <ul>
                <li>Guided step-by-step input</li>
                <li>Professional formatting</li>
                <li>ATS-compatible structure</li>
                <li>Fresher-friendly templates</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    c3, c4 = st.columns(2, gap="large")
    with c3:
        st.markdown("""
        <div class="feature-card">
            <div class="card-icon">📊</div>
            <h3>Application Tracker</h3>
            <p>Track all your job applications — company, role, date, and status — in one organized dashboard.</p>
            <ul>
                <li>Add, update, and manage applications</li>
                <li>Status tracking with filters and export</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown("""
        <div class="feature-card">
            <div class="card-icon">📁</div>
            <h3>Resume History</h3>
            <p>Browse all your previously generated and optimized resumes with timestamps and quick access.</p>
            <ul>
                <li>Version history for all resumes</li>
                <li>Download any past version</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    if not _api_ok:
        st.info(
            "Start **Ollama** locally to enable AI features. "
            "Run `ollama serve` in your terminal, then `ollama pull llama3.2`."
        )


# ════════════════════════════════════════════════════════════════════════════════
#  OPTIMIZE RESUME
# ════════════════════════════════════════════════════════════════════════════════

elif page == "optimize":
    st.title("Optimize Resume")
    st.markdown(
        '<p class="page-subtitle">'
        'Upload your resume and paste the target job description. AI will analyze, optimize, and tailor it for ATS.'
        '</p>',
        unsafe_allow_html=True,
    )

    # --- Input Section ---
    _section_header("📤", "Upload & Input", "Provide your resume and target job description")

    c1, c2 = st.columns(2, gap="large")
    with c1:
        uploaded = st.file_uploader(
            "Upload Your Resume",
            type=["pdf", "docx"],
            help="PDF or DOCX, max 10 MB",
        )
    with c2:
        jd = st.text_area(
            "Paste Job Description",
            height=200,
            placeholder="Paste the full job description here...",
            help="The more detail, the better the optimization.",
        )
        if jd:
            st.caption(f"{len(jd):,} characters")

    st.markdown("<div style='height: 8px'></div>", unsafe_allow_html=True)

    o1, o2 = st.columns(2, gap="large")
    with o1:
        want_cover = st.checkbox("Also generate a Cover Letter")
    with o2:
        template = st.selectbox("PDF Template", AVAILABLE_TEMPLATES, key="opt_tpl")

    st.divider()

    if st.button("🚀 Optimize Resume", use_container_width=True, type="primary"):
        if not _api_ok:
            st.error("Ollama is not running. Start it with `ollama serve`.")
        elif not uploaded:
            st.warning("Please upload your resume (PDF or DOCX).")
        elif not jd or not jd.strip():
            st.warning("Please paste the target job description.")
        else:
            try:
                with st.spinner("Parsing your resume..."):
                    resume_text = parse_resume(uploaded, uploaded.name)

                with st.spinner("Analyzing skills..."):
                    match = calculate_match_score(resume_text, jd)
                    st.session_state.match_result = match

                # --- Skill Match Analysis ---
                _section_header("📊", "Skill Match Analysis", "How well your resume matches the job")

                score = match.score
                s1, s2, s3 = st.columns(3, gap="medium")
                with s1:
                    if score >= 70:
                        st.metric("ATS Match Score", f"{score}%", delta="Good")
                    elif score >= 40:
                        st.metric("ATS Match Score", f"{score}%", delta="Fair", delta_color="off")
                    else:
                        st.metric("ATS Match Score", f"{score}%", delta="Low", delta_color="inverse")
                with s2:
                    st.metric("Matched Skills", len(match.matched))
                with s3:
                    st.metric("Missing Skills", len(match.missing))

                if match.matched:
                    with st.expander(f"✅ Matched Skills ({len(match.matched)})", expanded=True):
                        pills = " ".join(f'<span class="skill-pill">{s}</span>' for s in match.matched)
                        st.markdown(pills, unsafe_allow_html=True)

                if match.missing:
                    with st.expander(f"⚠️ Missing Skills ({len(match.missing)})", expanded=True):
                        pills = " ".join(f'<span class="skill-pill missing">{s}</span>' for s in match.missing)
                        st.markdown(pills, unsafe_allow_html=True)

                if match.category_breakdown:
                    with st.expander("📊 Category Breakdown"):
                        chart = {c: i["score"] for c, i in match.category_breakdown.items()}
                        st.bar_chart(chart, height=250)

                # --- Optimization ---
                prog = st.progress(0, text="Optimizing your resume...")
                prog.progress(30, text="Generating optimized content...")
                optimized = optimize_resume(resume_text, jd)
                prog.progress(100, text="Optimization complete.")
                st.session_state.optimized_resume = optimized

                # --- Resume Preview ---
                _section_header("👁️", "Resume Preview", "Review your optimized resume")
                pdf_bytes = None
                try:
                    pdf_bytes = generate_pdf(optimized, template)
                    st.markdown(get_pdf_preview_html(pdf_bytes), unsafe_allow_html=True)
                except Exception as e:
                    logger.warning(f"PDF preview failed: {e}")
                    _show_resume(optimized)

                # --- Download Actions ---
                st.divider()
                d1, d2, d3 = st.columns(3, gap="medium")
                with d1:
                    if pdf_bytes:
                        st.download_button(
                            "📥 Download PDF", pdf_bytes,
                            file_name=f"optimized_resume_{datetime.now():%Y%m%d_%H%M}.pdf",
                            mime="application/pdf", use_container_width=True,
                        )
                with d2:
                    st.download_button(
                        "📄 Download TXT", optimized,
                        file_name=f"optimized_resume_{datetime.now():%Y%m%d_%H%M}.txt",
                        use_container_width=True,
                    )
                with d3:
                    save_resume(optimized, "optimized")
                    st.success("✅ Saved to history.")

                # --- AI Suggestions ---
                with st.expander("💡 AI Improvement Suggestions"):
                    with st.spinner("Analyzing..."):
                        st.markdown(generate_suggestions(optimized, jd))

                # --- Cover Letter ---
                if want_cover:
                    with st.spinner("Generating cover letter..."):
                        cover = generate_cover_letter(optimized, jd)
                        st.session_state.cover_letter = cover
                    _section_header("✉️", "Cover Letter")
                    _show_resume(cover)
                    st.download_button(
                        "📥 Download Cover Letter", cover,
                        file_name=f"cover_letter_{datetime.now():%Y%m%d_%H%M}.txt",
                        use_container_width=True,
                    )

            except ResumeParseError as e:
                st.error(f"Resume Parse Error: {e}")
                logger.error(f"Parse error: {e}")
            except LLMError as e:
                st.error(f"AI Error: {e}")
                logger.error(f"LLM error: {e}")
            except Exception as e:
                st.error(f"Unexpected error: {e}")
                logger.exception("Optimize mode error")


# ════════════════════════════════════════════════════════════════════════════════
#  BUILD FROM SCRATCH
# ════════════════════════════════════════════════════════════════════════════════

elif page == "build":
    st.title("Build from Scratch")
    st.markdown(
        '<p class="page-subtitle">'
        'Fill in your details and AI will craft a professional, ATS-friendly resume.'
        '</p>',
        unsafe_allow_html=True,
    )

    # --- Personal Information ---
    _section_header("👤", "Personal Information", "Your basic contact details")
    c1, c2 = st.columns(2, gap="large")
    with c1:
        name = st.text_input("Full Name *", placeholder="e.g. John Doe")
        email = st.text_input("Email *", placeholder="e.g. johndoe@email.com")
        phone = st.text_input("Phone Number", placeholder="e.g. +91 9876543210")
    with c2:
        location = st.text_input("Location", placeholder="e.g. Hyderabad, Telangana")
        linkedin = st.text_input("LinkedIn URL", placeholder="e.g. linkedin.com/in/johndoe")
        github = st.text_input("GitHub URL", placeholder="e.g. github.com/johndoe")

    st.divider()

    # --- Education ---
    _section_header("🎓", "Education", "Academic qualifications")
    c1, c2 = st.columns(2, gap="large")
    with c1:
        degree = st.text_input("Degree / Qualification *", placeholder="e.g. B.Tech in CSE")
        college = st.text_input("College / University *", placeholder="e.g. IIT Hyderabad")
    with c2:
        grad_year = st.text_input("Year of Graduation", placeholder="e.g. 2025")
        cgpa = st.text_input("CGPA / Percentage", placeholder="e.g. 8.5 / 85%")

    st.divider()

    # --- Experience ---
    _section_header("💼", "Experience", "Optional — Work experience & internships")
    experience = st.text_area(
        "Work experience / internships", height=120,
        placeholder="e.g. Internship at XYZ as Python Developer (Jun 2024 - Aug 2024).\nWorked on building REST APIs...",
    )

    st.divider()

    # --- Projects ---
    _section_header("🛠️", "Projects", "Describe your key projects")
    projects = st.text_area(
        "Describe your projects", height=120,
        placeholder="e.g.\nProject: Chat App | Tech: Python, Flask, Socket.IO\nDescription: Built a real-time messaging app...",
    )

    st.divider()

    # --- Skills ---
    _section_header("⚡", "Skills", "Technical and soft skills")
    skills = st.text_area(
        "List your skills (comma separated)",
        placeholder="e.g. Python, Machine Learning, SQL, React, Git, Docker...",
    )

    st.divider()

    # --- Achievements ---
    _section_header("🏆", "Achievements & Certifications", "Optional — Awards, certs, extras")
    achievements = st.text_area(
        "Certifications / Achievements / Extra-curriculars",
        placeholder="e.g. AWS Certified Cloud Practitioner, Winner of XYZ Hackathon...",
    )

    st.divider()

    # --- Target JD ---
    _section_header("🎯", "Target Job Description", "Optional but recommended for tailored results")
    jd_scratch = st.text_area(
        "Job Description", height=150,
        placeholder="Paste the JD to tailor your resume to a specific role...",
        label_visibility="collapsed",
    )
    if jd_scratch:
        st.caption(f"{len(jd_scratch):,} characters")

    st.markdown("<div style='height: 8px'></div>", unsafe_allow_html=True)

    g1, g2 = st.columns(2, gap="large")
    with g1:
        want_cover2 = st.checkbox("Also generate a Cover Letter", key="cov2")
    with g2:
        template2 = st.selectbox("PDF Template", AVAILABLE_TEMPLATES, key="gen_tpl")

    st.divider()

    if st.button("🚀 Generate My Resume", use_container_width=True, type="primary"):
        if not _api_ok:
            st.error("Ollama is not running. Start it with `ollama serve`.")
        elif not name or not email or not degree or not college:
            st.warning("Please fill in all required (*) fields: Name, Email, Degree, College.")
        else:
            user_data = {
                "name": name, "email": email, "phone": phone,
                "location": location, "linkedin": linkedin, "github": github,
                "degree": degree, "college": college, "grad_year": grad_year, "cgpa": cgpa,
                "experience": experience, "projects": projects,
                "skills": skills, "achievements": achievements,
                "job_description": jd_scratch,
            }

            try:
                prog = st.progress(0, text="Generating your professional resume...")
                prog.progress(30, text="AI is crafting your resume...")
                resume = generate_resume_from_scratch(user_data)
                prog.progress(100, text="Resume generated.")
                st.session_state.generated_resume = resume

                # --- Resume Preview ---
                _section_header("👁️", "Resume Preview", "Your AI-generated resume")
                pdf_bytes = None
                try:
                    pdf_bytes = generate_pdf(resume, template2)
                    st.markdown(get_pdf_preview_html(pdf_bytes), unsafe_allow_html=True)
                except Exception as e:
                    logger.warning(f"PDF preview failed: {e}")
                    _show_resume(resume)

                # --- Download Actions ---
                st.divider()
                d1, d2, d3 = st.columns(3, gap="medium")
                with d1:
                    if pdf_bytes:
                        st.download_button(
                            "📥 Download PDF", pdf_bytes,
                            file_name=f"resume_{datetime.now():%Y%m%d_%H%M}.pdf",
                            mime="application/pdf", use_container_width=True,
                        )
                with d2:
                    st.download_button(
                        "📄 Download TXT", resume,
                        file_name=f"resume_{datetime.now():%Y%m%d_%H%M}.txt",
                        use_container_width=True,
                    )
                with d3:
                    save_resume(resume, "generated")
                    st.success("✅ Saved to history.")

                # --- AI Suggestions ---
                with st.expander("💡 AI Improvement Suggestions"):
                    with st.spinner("Analyzing..."):
                        st.markdown(generate_suggestions(resume, jd_scratch))

                # --- Cover Letter ---
                if want_cover2 and jd_scratch and jd_scratch.strip():
                    with st.spinner("Generating cover letter..."):
                        cover = generate_cover_letter(resume, jd_scratch)
                        st.session_state.cover_letter = cover
                    _section_header("✉️", "Cover Letter")
                    _show_resume(cover)
                    st.download_button(
                        "📥 Download Cover Letter", cover,
                        file_name=f"cover_letter_{datetime.now():%Y%m%d_%H%M}.txt",
                        use_container_width=True,
                    )

            except ValueError as e:
                st.warning(str(e))
            except LLMError as e:
                st.error(f"AI Error: {e}")
                logger.error(f"LLM error: {e}")
            except Exception as e:
                st.error(f"Unexpected error: {e}")
                logger.exception("Build mode error")


# ════════════════════════════════════════════════════════════════════════════════
#  APPLICATION TRACKER
# ════════════════════════════════════════════════════════════════════════════════

elif page == "tracker":
    st.title("Application Tracker")
    st.markdown(
        '<p class="page-subtitle">'
        'Track every job application — company, role, status, and dates — all in one place.'
        '</p>',
        unsafe_allow_html=True,
    )

    # --- Add New Application Form ---
    with st.form("add_app", clear_on_submit=True):
        _section_header("➕", "Add New Application", "Log a new job application")
        c1, c2, c3 = st.columns(3, gap="large")
        with c1:
            company = st.text_input("Company Name *", placeholder="e.g. Google")
            role = st.text_input("Job Role *", placeholder="e.g. SDE Intern")
        with c2:
            app_date = st.date_input("Application Date")
            status = st.selectbox("Status", APPLICATION_STATUSES)
        with c3:
            link = st.text_input("Job Link", placeholder="https://...")
            notes = st.text_input("Notes", placeholder="Applied via referral...")
        submitted = st.form_submit_button("Add Application", use_container_width=True, type="primary")

        if submitted:
            if not company or not role:
                st.warning("Company Name and Job Role are required.")
            else:
                try:
                    save_application({
                        "company": company, "role": role,
                        "date": str(app_date), "status": status,
                        "link": link, "notes": notes,
                    })
                    st.success(f"Saved: **{role}** at **{company}**")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to save: {e}")

    st.divider()

    # --- Load & Display Applications ---
    apps = load_applications()

    if not apps.empty:
        # --- Summary Metrics ---
        _section_header("📈", "Overview", "Your application statistics at a glance")
        m1, m2, m3, m4 = st.columns(4, gap="medium")
        with m1:
            st.metric("Total", len(apps))
        with m2:
            count_applied = len(apps[apps["status"] == "Applied"]) if "status" in apps.columns else 0
            st.metric("Applied", count_applied)
        with m3:
            count_interview = len(apps[apps["status"] == "Interview Scheduled"]) if "status" in apps.columns else 0
            st.metric("Interviews", count_interview)
        with m4:
            count_offers = len(apps[apps["status"] == "Offer Received"]) if "status" in apps.columns else 0
            st.metric("Offers", count_offers)

        # --- Status Chart ---
        if "status" in apps.columns:
            with st.expander("📊 Status Distribution Chart"):
                try:
                    import plotly.express as px
                    sc = apps["status"].value_counts().reset_index()
                    sc.columns = ["Status", "Count"]
                    fig = px.pie(
                        sc, values="Count", names="Status", hole=0.45,
                        color="Status",
                        color_discrete_map={
                            "Applied": "#0A66C2",
                            "Interview Scheduled": "#2E7D32",
                            "Under Review": "#F57F17",
                            "Rejected": "#C62828",
                            "Offer Received": "#1B5E20",
                            "Accepted": "#00695C",
                            "Withdrawn": "#9E9E9E",
                        },
                    )
                    fig.update_layout(
                        showlegend=True,
                        legend=dict(orientation="h", y=-0.3, x=0.5, xanchor="center", font=dict(size=10)),
                        margin=dict(t=10, b=10, l=10, r=10),
                        height=320,
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                    )
                    fig.update_traces(textinfo="value", textfont_size=12)
                    st.plotly_chart(fig, use_container_width=True)
                except ImportError:
                    st.warning("Install `plotly` for chart visualization: `pip install plotly`")

        st.divider()

        # --- Filters ---
        _section_header("🔍", "Filter Applications", "Search and filter your applications")
        f1, f2, f3 = st.columns([2, 2, 1], gap="large")
        with f1:
            filt = st.selectbox("Filter by Status", ["All"] + APPLICATION_STATUSES, key="filt")
        with f2:
            search = st.text_input("Search Company / Role", placeholder="Type to search...", key="srch")
        with f3:
            st.download_button(
                "📥 Export CSV",
                apps.to_csv(index=False).encode("utf-8"),
                file_name=f"applications_{datetime.now():%Y%m%d}.csv",
                mime="text/csv", use_container_width=True,
            )

        filtered = apps.copy()
        if filt != "All" and "status" in filtered.columns:
            filtered = filtered[filtered["status"] == filt]
        if search and search.strip():
            q = search.strip().lower()
            filtered = filtered[
                filtered["company"].str.lower().str.contains(q, na=False)
                | filtered["role"].str.lower().str.contains(q, na=False)
            ]

        st.divider()

        st.markdown(
            f'<p style="font-weight: 600; color: #191919; font-size: 0.95rem; margin-bottom: 12px;">'
            f'Applications ({len(filtered)} of {len(apps)})</p>',
            unsafe_allow_html=True,
        )

        if filtered.empty:
            st.info("No applications match your filter.")
        else:
            for idx in filtered.index:
                r = filtered.loc[idx]
                co = r.get("company", "Unknown")
                ro = r.get("role", "Unknown")
                cs = r.get("status", "Applied")
                lk = r.get("link", "")
                nt = r.get("notes", "")
                dt = str(r.get("date", ""))
                emoji = STATUS_COLORS.get(cs, "⚪")
                css_cls = STATUS_CSS_CLASS.get(cs, "status-applied")

                with st.container(border=True):
                    # Application header row
                    top1, top2 = st.columns([4, 1])
                    with top1:
                        st.markdown(f"**{co}** — {ro}")
                        info_parts = [f"📅 {dt}"]
                        if lk and lk.strip():
                            info_parts.append(f"[🔗 Link]({lk})")
                        st.caption(" · ".join(info_parts))
                        if nt and nt.strip():
                            st.caption(f"📝 {nt}")
                    with top2:
                        st.markdown(
                            f'<div class="status-badge {css_cls}">{emoji} {cs}</div>',
                            unsafe_allow_html=True,
                        )

                    # Action row
                    a1, a2, a3 = st.columns([3, 1, 1], gap="medium")
                    with a1:
                        ns = st.selectbox(
                            "Status", APPLICATION_STATUSES,
                            index=APPLICATION_STATUSES.index(cs) if cs in APPLICATION_STATUSES else 0,
                            key=f"s_{idx}", label_visibility="collapsed",
                        )
                    with a2:
                        if st.button("Update", key=f"u_{idx}", use_container_width=True):
                            if ns != cs:
                                if update_application_status(idx, ns):
                                    st.success(f"Updated to **{ns}**")
                                    st.rerun()
                                else:
                                    st.error("Failed to update.")
                            else:
                                st.info("Status unchanged.")
                    with a3:
                        if st.button("🗑️ Delete", key=f"d_{idx}", use_container_width=True):
                            st.session_state[f"cdel_{idx}"] = True

                    # Delete confirmation
                    if st.session_state.get(f"cdel_{idx}", False):
                        st.warning(f"Delete **{ro}** at **{co}**?")
                        y, n, _ = st.columns([1, 1, 4])
                        with y:
                            if st.button("Yes", key=f"cy_{idx}", use_container_width=True):
                                if delete_application(idx):
                                    st.session_state.pop(f"cdel_{idx}", None)
                                    st.rerun()
                        with n:
                            if st.button("Cancel", key=f"cn_{idx}", use_container_width=True):
                                st.session_state.pop(f"cdel_{idx}", None)
                                st.rerun()
    else:
        st.info("No applications tracked yet. Add your first application using the form above.")


# ════════════════════════════════════════════════════════════════════════════════
#  RESUME HISTORY
# ════════════════════════════════════════════════════════════════════════════════

elif page == "history":
    st.title("Resume History")
    st.markdown(
        '<p class="page-subtitle">'
        'Browse all your previously generated and optimized resumes with quick download access.'
        '</p>',
        unsafe_allow_html=True,
    )

    resumes = load_resumes()

    if resumes:
        st.metric("Total Resumes Saved", len(resumes))

        st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)

        for i, entry in enumerate(resumes):
            mode = "Generated" if entry.get("mode") == "generated" else "Optimized"
            ts = entry.get("timestamp", "Unknown")
            cc = entry.get("char_count", len(entry.get("content", "")))
            mode_icon = "📝" if entry.get("mode") == "generated" else "🔧"
            badge_cls = "generated" if entry.get("mode") == "generated" else "optimized"

            # Styled header for the expander
            with st.expander(f"{mode_icon} {mode} — {ts} ({cc:,} chars)", expanded=(i == 0)):
                content = entry.get("content", "")
                _show_resume(content)
                st.download_button(
                    "📥 Download TXT", content,
                    file_name=f"resume_{entry.get('mode', 'saved')}_{entry.get('id', i)}.txt",
                    key=f"dl_{entry.get('id', i)}",
                    use_container_width=True,
                )
    else:
        st.info("No resumes saved yet. Generate or optimize a resume to see it here.")


# ════════════════════════════════════════════════════════════════════════════════
#  FOOTER
# ════════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="custom-footer">
    <hr style="border: none; border-top: 1px solid #E0E0E0; margin-bottom: 16px;">
    <strong>AI Resume Generator</strong> v2.0 · Built with Streamlit & Local AI ·
    Resume analysis, optimization & career assistance — runs 100% on your machine.
</div>
""", unsafe_allow_html=True)