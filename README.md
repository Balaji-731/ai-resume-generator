# AI Resume Generator

A professional-grade, AI-powered resume optimization and generation platform — built with **Streamlit** and **Ollama (Local LLM)**. Designed for AI/ML roles with ATS-optimized, recruiter-ready PDF output.

GitHub Link: https://github.com/Balaji-731/ai-resume-generator
---

## Project Structure

```
ai_resume_generator/
├── app.py                  # Main Streamlit SaaS dashboard
├── config.py               # Centralized configuration & settings
├── logger.py               # Logging setup (file + console)
├── llm_helper.py           # Ollama (local LLM) integration with retry logic
├── resume_parser.py        # PDF/DOCX resume text extraction
├── resume_generator.py     # AI-powered resume generation from scratch
├── optimizer.py            # AI-powered resume optimization for JD
├── cover_letter.py         # AI-powered cover letter generation
├── skill_matcher.py        # Rule-based skill extraction & matching
├── pdf_generator.py        # Dual-engine PDF renderer (LaTeX + HTML)
├── storage.py              # Data persistence (JSON + CSV + Supabase)
├── auth.py                 # User authentication (Supabase)
├── supabase_client.py      # Supabase client setup
├── suggestions.py          # AI improvement suggestions engine
├── requirements.txt        # Python dependencies
├── .gitignore              # Git ignore rules
├── logs/                   # Auto-created: application logs
│   └── app.log
└── .streamlit/             # Streamlit configuration
```

---

## Features

### Mode 1: Optimize Existing Resume
- Upload a PDF/DOCX resume + paste a job description
- **AI-powered skill gap analysis** with category-wise breakdown chart
- **ATS match score** with visual badge (color-coded: Good / Fair / Low)
- **Intelligent resume rewriting** — action verbs, quantified achievements, keyword optimization
- **3 professional PDF templates** — ATS Classic, Modern, Developer
- Downloadable optimized resume (PDF + TXT)

### Mode 2: Build Resume from Scratch
- Guided step-by-step input (personal info, education, experience, projects, skills)
- **AI generates a complete professional resume** from provided details
- Skills auto-grouped into categories: Machine Learning & AI, Backend & Deployment, Programming Languages
- Tailored to specific job description (optional)
- Fresher-friendly: emphasizes projects, skills, and education when no experience provided

### AI Cover Letter
- One-click AI-generated cover letter aligned with the job description
- Professional tone with specific examples from the resume
- Available in both Optimize and Build modes

### Professional PDF Generation
- **Dual-engine architecture**: LaTeX (pdflatex) primary, HTML+xhtml2pdf fallback
- **3 templates**, each optimized for ATS scanners:

| Template      | Style                                                    |
|---------------|----------------------------------------------------------|
| ATS Classic   | Traditional single-column, ruled sections, serif-clean   |
| Modern        | Colored accent bar, blue section rules, contemporary     |
| Developer     | Left-border accent bars, strong hierarchy, tech-focused  |

- **Enforced section order**: Header → Summary → Skills → Experience → Projects → Education → Certifications → Achievements
- Automatic empty section removal
- Strictly 1-page layout with optimized margins and spacing

### Application Tracker
- Track job applications: company, role, date, status, link, notes
- Summary metrics dashboard (total, applied, interviews, offers)
- Persistent storage with Supabase

### Resume History
- Browse all previously generated/optimized resumes
- Timestamps and quick access
- Download any past version

### Authentication
- Secure sign-up / sign-in via Supabase Auth
- Per-user data isolation (resumes, applications, history)

---

## Tech Stack

| Component          | Technology                          |
|--------------------|-------------------------------------|
| Language           | Python 3.9+                         |
| UI Framework       | Streamlit (Professional SaaS theme) |
| AI / LLM           | Ollama (Local — privacy-first)      |
| PDF Engine (Primary)| LaTeX (pdflatex / MiKTeX)          |
| PDF Engine (Fallback)| xhtml2pdf (zero-setup)            |
| PDF Parsing        | pdfplumber                          |
| DOCX Parsing       | python-docx                         |
| Auth & Storage     | Supabase                            |
| Local Storage      | JSON + CSV                          |
| Data Analysis      | pandas                              |
| Icons              | Bootstrap Icons (CDN)               |
| Typography         | Inter (Google Fonts)                |

---

## Resume Formatting Engine

The PDF generator enforces industry-standard resume formatting:

### Section Order (Strict)
1. **Header** — Full name (large bold) + contact on single line (Email | Phone | Location | LinkedIn | GitHub)
2. **Professional Summary** — 2–3 concise, impactful lines
3. **Technical Skills** — Grouped by category (ML & AI / Backend & Deployment / Languages)
4. **Experience** — Action-verb bullets, measurable impact, 3–4 bullets per role
5. **Projects** — Problem → Tech → Result format, 3–4 bullets each
6. **Education** — Degree, university, year, CGPA in clean single block
7. **Certifications** — Only if content exists
8. **Achievements** — Only if content exists

### Design Principles
- Clean, minimal, single-column layout
- Consistent bullet style (• only)
- Equal spacing between sections
- No broken words, no text overflow
- Balanced white space — readable in 5–7 seconds
- Strictly 1 page

---

## Setup & Run

### 1. Clone or download the project

```bash
cd ai_resume_generator
```

### 2. Create virtual environment

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install & start Ollama (Local LLM)

```bash
# Install from https://ollama.com
ollama pull llama3          # or any supported model
ollama serve                # start the server
```

### 5. (Optional) Install LaTeX for premium PDF quality

Install [MiKTeX](https://miktex.org/download) for Overleaf-quality LaTeX PDFs. If not installed, the app automatically falls back to HTML+xhtml2pdf rendering.

### 6. Run the app

```bash
streamlit run app.py
```

The app opens at: **http://localhost:8501**

---

## How to Use

1. **Sign up / Sign in** on the authentication page
2. **Choose a mode** from the sidebar navigation
3. **Optimize**: Upload resume + paste JD → select template → click "Optimize Resume"
4. **Build**: Fill in your details → select template → click "Generate My Resume"
5. **Preview** the generated PDF inline
6. **Download** the resume (PDF/TXT) and/or cover letter
7. **Track** your applications in the Application Tracker

---

## Project Details

- **Title**: AI Resume Generator — Intelligent Resume Analysis, Optimization & Generation Platform
- **Domain**: Artificial Intelligence, Natural Language Processing, Career Assistance
- **Purpose**: Professional-grade tool for job seekers — automates resume creation, ATS optimization, and application tracking with local AI (no data leaves your machine)

---

## License

This project is built for academic and personal use.
