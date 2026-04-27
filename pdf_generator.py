"""
PDF Resume Generator — Professional Template Engine.

Dual-engine architecture:
  Primary  → LaTeX templates compiled with pdflatex (Overleaf quality)
  Fallback → HTML + CSS templates rendered with xhtml2pdf (zero-setup)

Templates (available in both engines):
  - ATS Classic : Traditional single-column, ruled sections, ATS-scannable
  - Modern      : Contemporary accents, colored headers, generous spacing
  - Developer   : Strong hierarchy with accent bars, technical emphasis

Section render order (enforced):
  header → summary → skills → experience → projects →
  education → certifications → achievements/other

Design system:
  Spacing  : 4pt tight · 8pt default · 12pt comfortable · 16pt spacious
  Body     : 9.5–10pt  ·  Entry title: 10pt bold  ·  Section header: 10.5–11pt
  Name     : 22–28pt depending on template
  Layout   : A4 (210 × 297 mm), margins 12–18 mm
"""

import re
import io
import os
import base64
import shutil
import subprocess
import tempfile
from html import escape as html_escape

from logger import get_logger

logger = get_logger(__name__)

# ─── Engine Availability ──────────────────────────────────────────────────────

_HAS_LATEX = shutil.which("pdflatex") is not None
if _HAS_LATEX:
    logger.info("pdflatex found — LaTeX PDF generation enabled")
else:
    logger.info("pdflatex not found — using HTML+xhtml2pdf fallback")

try:
    from xhtml2pdf import pisa
    _HAS_XHTML2PDF = True
except ImportError:
    _HAS_XHTML2PDF = False
    logger.warning("xhtml2pdf not installed — HTML fallback unavailable")

AVAILABLE_TEMPLATES = ["ATS Classic", "Modern", "Developer"]

# ─── Section Keyword Mapping ──────────────────────────────────────────────────

SECTION_KEYWORDS = {
    "summary": [
        "professional summary", "summary", "objective",
        "career objective", "profile", "about me", "career summary",
    ],
    "skills": [
        "technical skills", "skills", "core competencies",
        "technologies", "key skills", "core skills",
    ],
    "experience": [
        "experience", "work experience", "professional experience",
        "employment", "internships", "experience / internships",
        "experience/internships",
    ],
    "projects": [
        "projects", "personal projects", "key projects",
        "academic projects",
    ],
    "education": [
        "education", "academic background", "qualifications",
        "academic qualifications",
    ],
    "certifications": [
        "certifications", "certificates", "professional certifications",
        "certifications & achievements",
    ],
    "achievements": [
        "achievements", "awards", "honors",
        "achievements & certifications", "accomplishments",
    ],
}

SIDEBAR_TYPES = {"contact", "skills", "education", "certifications"}

SECTION_RENDER_ORDER = [
    "summary", "skills", "experience", "projects",
    "education", "certifications", "achievements", "other",
]


# ═══════════════════════════════════════════════════════════════════════════════
#  TEXT UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

def _is_bullet(line: str) -> bool:
    return bool(re.match(r"^\s*[-*>•]\s", line))


def _clean_bullet(line: str) -> str:
    return re.sub(r"^\s*[-*>•]\s*", "", line)


def _is_subheader(line: str) -> bool:
    stripped = line.strip()
    if not stripped or _is_bullet(line):
        return False
    if "|" in stripped:
        return True
    if re.search(r"\d{4}\s*[-\u2013\u2014]\s*(\d{4}|present|current)", stripped, re.I):
        return True
    parts = re.split(r"\s+[-\u2013\u2014]\s+", stripped)
    if len(parts) >= 2 and all(len(p) > 2 for p in parts):
        return True
    return False


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION PARSER
# ═══════════════════════════════════════════════════════════════════════════════

def _identify_section(line: str):
    cleaned = line.strip().lower()
    cleaned = re.sub(r"[=\-_*#~:]+$", "", cleaned).strip()
    cleaned = re.sub(r"^[=\-_*#~]+", "", cleaned).strip()
    if not cleaned or len(cleaned) > 60:
        return None
    for stype, keywords in SECTION_KEYWORDS.items():
        for kw in keywords:
            if cleaned == kw or cleaned.startswith(kw + ":") or cleaned.startswith(kw + " "):
                return stype
    orig = line.strip()
    if orig.isupper() and 3 < len(orig) < 50 and not orig.startswith(("-", "*", ">")):
        return "other"
    return None


def _parse_sections(text: str):
    lines = text.strip().split("\n")
    sections, contact_lines, current = [], [], None
    found_first = False

    for line in lines:
        stype = _identify_section(line)
        if stype and (found_first or stype != "other"):
            if current:
                sections.append(current)
            if not found_first and contact_lines:
                clean = [l for l in contact_lines if l.strip()]
                if clean:
                    sections.insert(0, ("contact", "Contact", clean))
            found_first = True
            current = (stype, line.strip(), [])
        elif not found_first:
            contact_lines.append(line)
        elif current:
            current[2].append(line)

    if current:
        sections.append(current)
    elif contact_lines:
        clean = [l for l in contact_lines if l.strip()]
        if clean:
            sections.append(("contact", "Contact", clean))
    return sections


# ═══════════════════════════════════════════════════════════════════════════════
#  COMMON HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _extract_contact(sections):
    name, contact_lines = "", []
    for stype, _, lines in sections:
        if stype == "contact" and lines:
            name = lines[0].strip()
            contact_lines = [l.strip() for l in lines[1:] if l.strip()]
            break
    return name, contact_lines


def _split_entry_header(text: str):
    if "|" in text:
        parts = [p.strip() for p in text.split("|")]
        if re.search(r"\d{4}", parts[-1]):
            return " | ".join(parts[:-1]), parts[-1]
        return " | ".join(parts), ""
    dp = (
        r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\.?\s*\d{4}"
        r"|\d{1,2}/\d{4}|\d{4}"
    )
    match = re.search(
        rf"({dp})\s*[-\u2013\u2014]\s*({dp}|Present|Current|Ongoing)",
        text, re.I,
    )
    if match:
        return text[:match.start()].rstrip(" -\u2013\u2014,").strip(), match.group(0).strip()
    return text, ""


def _order_sections(sections):
    """Reorder non-contact sections into the canonical resume order.
    Drops empty sections automatically.
    """
    by_type = {}
    for stype, title, lines in sections:
        if stype == "contact":
            continue
        # Skip empty sections
        content = [l for l in lines if l.strip()]
        if not content:
            continue
        by_type.setdefault(stype, []).append((stype, title, lines))
    ordered = []
    for stype in SECTION_RENDER_ORDER:
        ordered.extend(by_type.pop(stype, []))
    for remaining in by_type.values():
        ordered.extend(remaining)
    return ordered


def _clean_title(title: str) -> str:
    return re.sub(r"[=\-_*#~]+", "", title).strip()


# ═══════════════════════════════════════════════════════════════════════════════
#  LATEX ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

def _sanitize_for_latex(text: str) -> str:
    """Normalize Unicode before LaTeX escaping."""
    _MAP = {
        "\u2018": "'", "\u2019": "'", "\u201c": "``", "\u201d": "''",
        "\u2013": "--", "\u2014": "---", "\u2022": "", "\u2023": "",
        "\u25cf": "", "\u25cb": "", "\u2026": "...", "\u00a0": " ",
        "\u2192": "->", "\u00b7": "-", "\u27a4": ">", "\u2b50": "*",
        "\u2728": "*", "\u25aa": "", "\u25ba": ">", "\u25b6": ">",
    }
    for old, new in _MAP.items():
        text = text.replace(old, new)
    # Strip markdown bold/italic
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"__(.+?)__", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"_(.+?)_", r"\1", text)
    return text


def _escape_latex(text: str) -> str:
    """Escape LaTeX special characters."""
    text = text.replace("\\", r"\textbackslash{}")
    for old, new in {
        "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
        "_": r"\_", "{": r"\{", "}": r"\}",
        "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
    }.items():
        text = text.replace(old, new)
    return text


def _ltx(text: str) -> str:
    """Shorthand: sanitize + escape for LaTeX."""
    return _escape_latex(_sanitize_for_latex(text))


def _render_body_latex(lines):
    """Convert section body lines to LaTeX source."""
    parts = []
    in_itemize = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_itemize:
                parts.append(r"\end{itemize}")
                in_itemize = False
            continue

        if _is_bullet(line):
            if not in_itemize:
                parts.append(r"\begin{itemize}")
                in_itemize = True
            parts.append(f"  \\item {_ltx(_clean_bullet(line))}")

        elif _is_subheader(stripped):
            if in_itemize:
                parts.append(r"\end{itemize}")
                in_itemize = False
            left, right = _split_entry_header(stripped)
            left = _ltx(left)
            right = _ltx(right)
            if right:
                right = right.replace(" - ", " -- ")
                parts.append(f"\\textbf{{{left}}} \\hfill {right} \\\\")
            else:
                parts.append(f"\\textbf{{{left}}} \\\\")

        else:
            if in_itemize:
                parts.append(r"\end{itemize}")
                in_itemize = False
            parts.append(_ltx(stripped))

    if in_itemize:
        parts.append(r"\end{itemize}")
    return "\n".join(parts)


# ── LaTeX Preambles ───────────────────────────────────────────────────────────

_PREAMBLE_ATS_CLASSIC = r"""
\documentclass[10pt,a4paper]{article}
\usepackage[top=10mm,bottom=10mm,left=14mm,right=14mm]{geometry}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage{enumitem}
\usepackage{titlesec}
\usepackage{hyperref}

\pagestyle{empty}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0pt}

\titleformat{\section}
  {\vspace{-4pt}\normalsize\bfseries\scshape\raggedright}
  {}{0em}
  {}[\titlerule\vspace{-4pt}]
\titlespacing*{\section}{0pt}{7pt}{3pt}

\setlist[itemize]{
  leftmargin=14pt, topsep=1pt, itemsep=0pt,
  parsep=0pt, partopsep=0pt, label=\textbullet
}
\hypersetup{colorlinks=false, pdfborder={0 0 0}}
"""

_PREAMBLE_MODERN = r"""
\documentclass[10pt,a4paper]{article}
\usepackage[top=10mm,bottom=10mm,left=14mm,right=14mm]{geometry}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage{enumitem}
\usepackage{titlesec}
\usepackage{hyperref}
\usepackage{xcolor}

\pagestyle{empty}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0pt}

\definecolor{accent}{RGB}{14,165,233}
\definecolor{heading}{RGB}{15,23,42}
\definecolor{subtext}{RGB}{100,116,139}

\titleformat{\section}
  {\vspace{-2pt}\normalsize\bfseries\color{heading}}
  {}{0em}
  {}[{\color{accent}\titlerule}\vspace{-2pt}]
\titlespacing*{\section}{0pt}{8pt}{3pt}

\setlist[itemize]{
  leftmargin=14pt, topsep=1pt, itemsep=0pt,
  parsep=0pt, partopsep=0pt,
  label={\color{accent}\textbullet}
}
\hypersetup{colorlinks=true, urlcolor=accent, pdfborder={0 0 0}}
"""

_PREAMBLE_DEVELOPER = r"""
\documentclass[10pt,a4paper]{article}
\usepackage[top=10mm,bottom=10mm,left=14mm,right=14mm]{geometry}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage{enumitem}
\usepackage{titlesec}
\usepackage{hyperref}
\usepackage{xcolor}

\pagestyle{empty}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0pt}

\definecolor{accent}{RGB}{79,70,229}
\definecolor{heading}{RGB}{17,24,39}
\definecolor{subtext}{RGB}{107,114,128}

\titleformat{\section}
  {\vspace{-2pt}\normalsize\bfseries}
  {}{0em}
  {\color{accent}\vrule width 3pt height 10pt depth 2pt\hspace{8pt}\color{heading}}
\titlespacing*{\section}{0pt}{7pt}{3pt}

\setlist[itemize]{
  leftmargin=14pt, topsep=1pt, itemsep=0pt,
  parsep=0pt, partopsep=0pt, label=\textbullet
}
\hypersetup{colorlinks=false, pdfborder={0 0 0}}
"""


# ── LaTeX Template Builders ───────────────────────────────────────────────────

def _build_ats_classic_latex(sections):
    name, contacts = _extract_contact(sections)
    name_tex = _ltx(name) if name else "Resume"
    contact_tex = " \\,|\\, ".join(_ltx(c) for c in contacts)

    header = (
        "\\begin{center}\n"
        f"  {{\\LARGE\\bfseries {name_tex}}} \\\\[2pt]\n"
        f"  {{\\small {contact_tex}}}\n"
        "\\end{center}\n\\vspace{-2pt}\n"
    )

    body_parts = []
    for stype, title, lines in _order_sections(sections):
        clean = _ltx(_clean_title(title))
        body_parts.append(f"\\section{{{clean}}}")
        body_parts.append(_render_body_latex(lines))

    return _PREAMBLE_ATS_CLASSIC + "\n\\begin{document}\n" + header + "\n".join(body_parts) + "\n\\end{document}"


def _build_modern_latex(sections):
    name, contacts = _extract_contact(sections)
    name_tex = _ltx(name) if name else "Resume"
    contact_tex = " \\;\\textbullet\\; ".join(_ltx(c) for c in contacts)

    header = (
        "\\begin{center}\n"
        f"  {{\\LARGE\\bfseries\\color{{heading}} {name_tex}}} \\\\[3pt]\n"
        "  {\\color{accent}\\rule{45pt}{2pt}} \\\\[4pt]\n"
        f"  {{\\small\\color{{subtext}} {contact_tex}}}\n"
        "\\end{center}\n\\vspace{0pt}\n"
    )

    body_parts = []
    for stype, title, lines in _order_sections(sections):
        clean = _ltx(_clean_title(title))
        body_parts.append(f"\\section{{{clean}}}")
        body_parts.append(_render_body_latex(lines))

    return _PREAMBLE_MODERN + "\n\\begin{document}\n" + header + "\n".join(body_parts) + "\n\\end{document}"


def _build_developer_latex(sections):
    name, contacts = _extract_contact(sections)
    name_tex = _ltx(name) if name else "Resume"
    contact_tex = " \\,|\\, ".join(_ltx(c) for c in contacts)

    header = (
        f"{{\\LARGE\\bfseries\\color{{heading}} {name_tex}}} \\\\[2pt]\n"
        "{\\color{accent}\\rule{45pt}{2pt}} \\\\[3pt]\n"
        f"{{\\small\\color{{subtext}} {contact_tex}}}\n"
        "\\vspace{4pt}\n"
    )

    body_parts = []
    for stype, title, lines in _order_sections(sections):
        clean = _ltx(_clean_title(title))
        body_parts.append(f"\\section{{{clean}}}")
        body_parts.append(_render_body_latex(lines))

    return _PREAMBLE_DEVELOPER + "\n\\begin{document}\n" + header + "\n".join(body_parts) + "\n\\end{document}"


# ── LaTeX Compiler ────────────────────────────────────────────────────────────

def _latex_to_pdf(latex_source: str) -> bytes:
    """Compile LaTeX source to PDF via pdflatex."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_path = os.path.join(tmpdir, "resume.tex")
        pdf_path = os.path.join(tmpdir, "resume.pdf")

        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(latex_source)

        try:
            subprocess.run(
                ["pdflatex", "-interaction=nonstopmode",
                 "--disable-installer",
                 "-output-directory", tmpdir, tex_path],
                capture_output=True, text=True, timeout=30, cwd=tmpdir,
            )
        except FileNotFoundError:
            raise RuntimeError("pdflatex not found in PATH")
        except subprocess.TimeoutExpired:
            raise RuntimeError("LaTeX compilation timed out (30s)")

        if not os.path.exists(pdf_path):
            log_path = os.path.join(tmpdir, "resume.log")
            log_tail = ""
            if os.path.exists(log_path):
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    log_tail = f.read()[-600:]
            raise RuntimeError(f"LaTeX compilation failed.\n{log_tail}")

        with open(pdf_path, "rb") as f:
            return f.read()


# ═══════════════════════════════════════════════════════════════════════════════
#  HTML FALLBACK ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

def _sanitize_html(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"__(.+?)__", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"_(.+?)_", r"\1", text)
    for old, new in {
        "\u2022": "-", "\u2023": "-", "\u25cf": "-", "\u25cb": "o",
        "\u2713": "v", "\u2717": "x", "\u00b7": "-",
    }.items():
        text = text.replace(old, new)
    return html_escape(text)


def _render_body_html(lines):
    parts, in_list = [], False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_list:
                parts.append("</ul>")
                in_list = False
            continue
        if _is_bullet(line):
            if not in_list:
                parts.append('<ul class="bullets">')
                in_list = True
            parts.append(f"  <li>{_sanitize_html(_clean_bullet(line))}</li>")
        elif _is_subheader(stripped):
            if in_list:
                parts.append("</ul>")
                in_list = False
            left, right = _split_entry_header(stripped)
            left, right = _sanitize_html(left), _sanitize_html(right)
            if right:
                parts.append(
                    '<table class="entry-row"><tr>'
                    f'<td class="entry-left">{left}</td>'
                    f'<td class="entry-right">{right}</td>'
                    "</tr></table>"
                )
            else:
                parts.append(f'<div class="entry-title">{left}</div>')
        else:
            if in_list:
                parts.append("</ul>")
                in_list = False
            parts.append(f'<p class="body-text">{_sanitize_html(stripped)}</p>')
    if in_list:
        parts.append("</ul>")
    return "\n".join(parts)


# ── HTML/CSS Templates ───────────────────────────────────────────────────────

_CSS_ATS = """
@page{size:A4;margin:10mm 14mm}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:Helvetica,Arial,sans-serif;font-size:9.5pt;line-height:1.45;color:#2d2d2d}
.name{font-size:24pt;font-weight:bold;text-align:center;color:#111;margin-bottom:3px;letter-spacing:.5px}
.contact-line{text-align:center;font-size:8.5pt;color:#555;margin-bottom:2px;line-height:1.4}
.header-rule{border:none;border-top:1.5px solid #222;margin:6px 0 8px}
.section{margin-bottom:2px}
.section-title{font-size:10pt;font-weight:bold;text-transform:uppercase;letter-spacing:1.5px;color:#111;border-bottom:1.2px solid #444;padding-bottom:2px;margin-top:8px;margin-bottom:4px}
.entry-row{width:100%;border:none;margin-bottom:0px}.entry-row td{border:none;padding:1px 0}
.entry-left{font-weight:bold;font-size:9.5pt;color:#1a1a1a;text-align:left}
.entry-right{font-size:8.5pt;color:#666;text-align:right;white-space:nowrap}
.entry-title{font-weight:bold;font-size:9.5pt;color:#1a1a1a;margin-bottom:0px}
.body-text{font-size:9pt;color:#333;line-height:1.40;margin-bottom:1px}
ul.bullets{margin:1px 0 3px 16px;padding:0}
ul.bullets li{font-size:9pt;color:#333;line-height:1.40;margin-bottom:0.5px}
"""

_CSS_MODERN = """
@page{size:A4;margin:10mm 14mm}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:Helvetica,Arial,sans-serif;font-size:9pt;line-height:1.40;color:#334155}
.name{font-size:26pt;font-weight:bold;text-align:center;color:#0f172a;margin-bottom:4px;letter-spacing:.3px}
.accent-bar{width:45px;height:2.5px;background-color:#0ea5e9;margin:0 auto 6px auto}
.contact-line{text-align:center;font-size:8.5pt;color:#64748b;margin-bottom:2px;line-height:1.4}
.section{margin-bottom:2px}
.section-title{font-size:10pt;font-weight:bold;text-transform:uppercase;letter-spacing:1px;color:#0f172a;border-bottom:1.5px solid #0ea5e9;padding-bottom:2px;margin-top:8px;margin-bottom:4px}
.entry-row{width:100%;border:none;margin-bottom:0px}.entry-row td{border:none;padding:1px 0}
.entry-left{font-weight:bold;font-size:9.5pt;color:#0f172a;text-align:left}
.entry-right{font-size:8.5pt;color:#64748b;text-align:right;white-space:nowrap}
.entry-title{font-weight:bold;font-size:9.5pt;color:#0f172a;margin-bottom:0px}
.body-text{font-size:9pt;color:#334155;line-height:1.40;margin-bottom:1px}
ul.bullets{margin:1px 0 3px 16px;padding:0}
ul.bullets li{font-size:9pt;color:#334155;line-height:1.40;margin-bottom:0.5px}
"""

_CSS_DEV = """
@page{size:A4;margin:10mm 14mm}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:Helvetica,Arial,sans-serif;font-size:9.5pt;line-height:1.45;color:#374151}
.header-block{margin-bottom:8px}
.name{font-size:26pt;font-weight:bold;color:#111827;margin-bottom:3px}
.accent-underline{width:50px;height:2.5px;background-color:#4f46e5;margin-bottom:4px}
.contact-line{font-size:8.5pt;color:#6b7280;margin-bottom:1px;line-height:1.4}
.section{margin-bottom:2px}
.section-title{font-size:10pt;font-weight:bold;text-transform:uppercase;letter-spacing:1px;color:#111827;padding-left:10px;border-left:3px solid #4f46e5;margin-top:8px;margin-bottom:4px}
.entry-row{width:100%;border:none;margin-bottom:0px}.entry-row td{border:none;padding:1px 0}
.entry-left{font-weight:bold;font-size:9.5pt;color:#111827;text-align:left}
.entry-right{font-size:8.5pt;color:#6b7280;text-align:right;white-space:nowrap}
.entry-title{font-weight:bold;font-size:9.5pt;color:#111827;margin-bottom:0px}
.body-text{font-size:9pt;color:#374151;line-height:1.40;margin-bottom:1px}
ul.bullets{margin:1px 0 3px 16px;padding:0}
ul.bullets li{font-size:9pt;color:#374151;line-height:1.40;margin-bottom:0.5px}
"""


def _build_ats_classic_html(sections):
    name, contacts = _extract_contact(sections)
    name_h = _sanitize_html(name) if name else "Resume"
    contact_h = " &middot; ".join(_sanitize_html(c) for c in contacts)
    body = []
    for stype, title, lines in _order_sections(sections):
        ct = html_escape(_clean_title(title).upper())
        body.append(f'<div class="section"><div class="section-title">{ct}</div>')
        body.append(_render_body_html(lines))
        body.append("</div>")
    return (
        f'<!DOCTYPE html><html><head><meta charset="UTF-8"><style>{_CSS_ATS}</style></head><body>'
        f'<div class="name">{name_h}</div>'
        f'<div class="contact-line">{contact_h}</div>'
        f'<hr class="header-rule">'
        + "\n".join(body)
        + "</body></html>"
    )


def _build_modern_html(sections):
    name, contacts = _extract_contact(sections)
    name_h = _sanitize_html(name) if name else "Resume"
    contact_h = " &middot; ".join(_sanitize_html(c) for c in contacts)
    body = []
    for stype, title, lines in _order_sections(sections):
        ct = html_escape(_clean_title(title).upper())
        body.append(f'<div class="section"><div class="section-title">{ct}</div>')
        body.append(_render_body_html(lines))
        body.append("</div>")
    return (
        f'<!DOCTYPE html><html><head><meta charset="UTF-8"><style>{_CSS_MODERN}</style></head><body>'
        f'<div class="name">{name_h}</div>'
        f'<div class="accent-bar"></div>'
        f'<div class="contact-line">{contact_h}</div>'
        + "\n".join(body)
        + "</body></html>"
    )


def _build_developer_html(sections):
    name, contacts = _extract_contact(sections)
    name_h = _sanitize_html(name) if name else "Resume"
    contact_h = " &nbsp;|&nbsp; ".join(_sanitize_html(c) for c in contacts)
    body = []
    for stype, title, lines in _order_sections(sections):
        ct = html_escape(_clean_title(title).upper())
        body.append(f'<div class="section"><div class="section-title">{ct}</div>')
        body.append(_render_body_html(lines))
        body.append("</div>")
    return (
        f'<!DOCTYPE html><html><head><meta charset="UTF-8"><style>{_CSS_DEV}</style></head><body>'
        f'<div class="header-block"><div class="name">{name_h}</div>'
        f'<div class="accent-underline"></div>'
        f'<div class="contact-line">{contact_h}</div></div>'
        + "\n".join(body)
        + "</body></html>"
    )


def _html_to_pdf(html_string: str) -> bytes:
    buf = io.BytesIO()
    pisa.CreatePDF(html_string, dest=buf, encoding="utf-8")
    return buf.getvalue()


# ═══════════════════════════════════════════════════════════════════════════════
#  PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

_LATEX_BUILDERS = {
    "ATS Classic": _build_ats_classic_latex,
    "Modern": _build_modern_latex,
    "Developer": _build_developer_latex,
}

_HTML_BUILDERS = {
    "ATS Classic": _build_ats_classic_html,
    "Modern": _build_modern_html,
    "Developer": _build_developer_html,
}


def generate_pdf(resume_text: str, template: str = "ATS Classic") -> bytes:
    """
    Generate a professional PDF resume.

    Uses LaTeX (pdflatex) when available for Overleaf-quality output.
    Falls back to HTML+xhtml2pdf when LaTeX is not installed.

    Args:
        resume_text: Plain-text resume content.
        template: Template name — ATS Classic, Modern, or Developer.

    Returns:
        PDF content as bytes.
    """
    sections = _parse_sections(resume_text)
    logger.info(f"Generating PDF — template: {template}, sections: {len(sections)}, engine: {'LaTeX' if _HAS_LATEX else 'HTML'}")

    # ── Try LaTeX first ──────────────────────────────────────────────────
    if _HAS_LATEX:
        try:
            build_fn = _LATEX_BUILDERS.get(template, _build_ats_classic_latex)
            latex_src = build_fn(sections)
            pdf_bytes = _latex_to_pdf(latex_src)
            logger.info(f"LaTeX PDF generated: {len(pdf_bytes)} bytes")
            return pdf_bytes
        except Exception as e:
            logger.warning(f"LaTeX compilation failed ({e}), falling back to HTML")

    # ── HTML + xhtml2pdf fallback ────────────────────────────────────────
    if _HAS_XHTML2PDF:
        build_fn = _HTML_BUILDERS.get(template, _build_ats_classic_html)
        html_src = build_fn(sections)
        pdf_bytes = _html_to_pdf(html_src)
        logger.info(f"HTML PDF generated: {len(pdf_bytes)} bytes")
        return pdf_bytes

    raise RuntimeError(
        "No PDF engine available. "
        "Install LaTeX (MiKTeX) for premium quality, "
        "or run: pip install xhtml2pdf"
    )


def get_pdf_preview_html(pdf_bytes: bytes, height: int = 650) -> str:
    """Generate an HTML iframe to preview a PDF inline in Streamlit."""
    b64 = base64.b64encode(pdf_bytes).decode()
    return (
        f'<iframe src="data:application/pdf;base64,{b64}" '
        f'width="100%" height="{height}px" '
        f'style="border: 1px solid #e2e8f0; border-radius: 12px;" '
        f'type="application/pdf"></iframe>'
    )
