# 🤖 AI Resume Generator

An intelligent system for resume analysis, optimization, and job application assistance — powered by **Google Gemini AI**.

---

## 📁 Project Structure

```
ai_resume_generator/
├── app.py                  # Main Streamlit UI application
├── config.py               # Centralized configuration & settings
├── logger.py               # Logging setup (file + console)
├── llm_helper.py           # Gemini API integration with retry logic
├── resume_parser.py        # PDF/DOCX resume text extraction
├── resume_generator.py     # AI-powered resume generation from scratch
├── optimizer.py             # AI-powered resume optimization for JD
├── cover_letter.py         # AI-powered cover letter generation
├── skill_matcher.py        # Rule-based skill extraction & matching
├── storage.py              # Data persistence (JSON + CSV)
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template
├── .gitignore              # Git ignore rules
├── data/                   # Auto-created: stored resumes & applications
│   ├── resumes.json
│   └── applications.csv
└── logs/                   # Auto-created: application logs
    └── app.log
```

---

## ✨ Features

### 📝 Mode 1: Optimize Existing Resume
- Upload a PDF/DOCX resume + paste a job description
- **AI-powered skill gap analysis** with category-wise breakdown chart
- **ATS match score** with visual badge (color-coded)
- **Intelligent resume rewriting** — action verbs, keywords, quantified achievements
- Downloadable optimized resume

### ✨ Mode 2: Build Resume from Scratch
- Guided step-by-step input collection (personal info, education, projects, skills)
- **AI generates a complete professional resume** from provided details
- Tailored to specific job description (optional)
- Fresher-friendly: emphasizes projects, skills, and education

### 📨 AI Cover Letter
- One-click AI-generated cover letter aligned with the job description
- Professional tone with specific examples from the resume
- Available in both modes

### 📊 Application Tracker
- Track job applications: company, role, date, status, link, notes
- Summary metrics dashboard (total, applied, interviews, offers)
- CSV-based persistent storage

### 📂 Resume History
- Browse all previously generated/optimized resumes
- Timestamps and character counts
- Download any past version

---

## 🛠️ Tech Stack

| Component          | Technology                 |
|--------------------|----------------------------|
| Language           | Python 3.9+                |
| UI Framework       | Streamlit                  |
| AI / LLM           | Google Gemini 1.5 Flash    |
| PDF Parsing        | pdfplumber                 |
| DOCX Parsing       | python-docx                |
| Data Storage       | JSON + CSV (local files)   |
| Data Analysis      | pandas                     |
| Config Management  | python-dotenv              |

---

## 🚀 Setup & Run

### 1. Clone or download the project

```bash
cd ai_resume_generator
```

### 2. Create virtual environment (recommended)

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Get your FREE Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com)
2. Sign in with your Google account
3. Click **"Get API Key"** → **"Create API key"**
4. Copy the key

### 5. (Optional) Set up environment variables

```bash
cp .env.example .env
# Edit .env and paste your API key
```

Or simply paste the key in the app sidebar when it starts.

### 6. Run the app

```bash
streamlit run app.py
```

The app opens at: **http://localhost:8501**

---

## 📸 How to Use

1. **Enter your API key** in the sidebar (or set via `.env`)
2. **Choose a mode** from the sidebar navigation
3. **Mode 1**: Upload resume + paste JD → click "Optimize Resume"
4. **Mode 2**: Fill in your details → click "Generate My Resume"
5. **Download** the generated resume and/or cover letter
6. **Track** your applications in the Application Tracker

---

## 📝 Project Details

- **Title**: AI Resume Generator: An Intelligent System for Resume Analysis, Optimization, and Job Application Assistance
- **Domain**: Artificial Intelligence, Natural Language Processing, Career Assistance
- **Purpose**: Academic mini project with real-world applicability — automates resume creation and optimization for job seekers

---

## 📄 License

This project is built for academic and personal use.
