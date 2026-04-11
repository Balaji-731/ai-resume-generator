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
#  MINIMAL CSS — only font + hide defaults
# ════════════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body { font-family: 'Inter', sans-serif !important; }
#MainMenu, footer, header { visibility: hidden; }
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
    st.title("📄 Resume Generator")
    st.caption("AI-Powered Career Tools · v2.0")

    st.divider()

    # System status
    if _api_ok:
        st.success("✅ Ollama Connected", icon="🟢")
    else:
        st.error("❌ Ollama Offline", icon="🔴")
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
    st.caption("Powered by Ollama · Built with Streamlit")

page = _NAV_MAP[st.session_state.nav_selection]


# ════════════════════════════════════════════════════════════════════════════════
#  HOME
# ════════════════════════════════════════════════════════════════════════════════

if page == "home":
    st.title("Welcome")
    st.markdown("Intelligent resume analysis, optimization, and career assistance — powered by local AI.")

    st.divider()

    c1, c2 = st.columns(2, gap="medium")
    with c1:
        with st.container(border=True):
            st.subheader("🔧 Optimize Existing Resume")
            st.markdown(
                "Upload your resume and a job description. AI will analyze, "
                "optimize, and tailor it for ATS."
            )
            st.markdown("""
- Skill gap analysis with visual charts
- ATS-friendly bullet point rewriting
- Job-specific keyword optimization
- Optional AI cover letter generation
""")

    with c2:
        with st.container(border=True):
            st.subheader("📝 Build Resume from Scratch")
            st.markdown(
                "No resume? Fill in guided fields and AI will generate "
                "a complete professional resume."
            )
            st.markdown("""
- Guided step-by-step input
- Professional formatting
- ATS-compatible structure
- Fresher-friendly templates
""")

    c3, c4 = st.columns(2, gap="medium")
    with c3:
        with st.container(border=True):
            st.subheader("📊 Application Tracker")
            st.markdown(
                "Track all your job applications — company, role, date, and "
                "status — in one organized dashboard."
            )
            st.markdown("""
- Add, update, and manage applications
- Status tracking with filters and export
""")

    with c4:
        with st.container(border=True):
            st.subheader("📁 Resume History")
            st.markdown(
                "Browse all your previously generated and optimized resumes "
                "with timestamps and quick access."
            )
            st.markdown("""
- Version history for all resumes
- Download any past version
""")

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
        "Upload your resume and paste the target job description. "
        "AI will analyze, optimize, and tailor it for ATS."
    )

    st.divider()

    # --- Input Section ---
    c1, c2 = st.columns(2, gap="medium")
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

    o1, o2 = st.columns(2, gap="medium")
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
                st.subheader("Skill Match Analysis")

                score = match.score
                s1, s2, s3 = st.columns(3)
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
                        st.markdown(", ".join(f"`{s}`" for s in match.matched))

                if match.missing:
                    with st.expander(f"❌ Missing Skills ({len(match.missing)})", expanded=True):
                        st.markdown(", ".join(f"`{s}`" for s in match.missing))

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
                st.subheader("Resume Preview")
                pdf_bytes = None
                try:
                    pdf_bytes = generate_pdf(optimized, template)
                    st.markdown(get_pdf_preview_html(pdf_bytes), unsafe_allow_html=True)
                except Exception as e:
                    logger.warning(f"PDF preview failed: {e}")
                    _show_resume(optimized)

                # --- Download Actions ---
                st.divider()
                d1, d2, d3 = st.columns(3)
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
                    st.subheader("Cover Letter")
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
    st.markdown("Fill in your details and AI will craft a professional, ATS-friendly resume.")

    st.divider()

    # --- Personal Information ---
    st.subheader("👤 Personal Information")
    c1, c2 = st.columns(2, gap="medium")
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
    st.subheader("🎓 Education")
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        degree = st.text_input("Degree / Qualification *", placeholder="e.g. B.Tech in CSE")
        college = st.text_input("College / University *", placeholder="e.g. IIT Hyderabad")
    with c2:
        grad_year = st.text_input("Year of Graduation", placeholder="e.g. 2025")
        cgpa = st.text_input("CGPA / Percentage", placeholder="e.g. 8.5 / 85%")

    st.divider()

    # --- Experience ---
    st.subheader("💼 Experience")
    st.caption("Optional")
    experience = st.text_area(
        "Work experience / internships", height=120,
        placeholder="e.g. Internship at XYZ as Python Developer (Jun 2024 - Aug 2024).\nWorked on building REST APIs...",
    )

    st.divider()

    # --- Projects ---
    st.subheader("🛠️ Projects")
    projects = st.text_area(
        "Describe your projects", height=120,
        placeholder="e.g.\nProject: Chat App | Tech: Python, Flask, Socket.IO\nDescription: Built a real-time messaging app...",
    )

    st.divider()

    # --- Skills ---
    st.subheader("⚡ Skills")
    skills = st.text_area(
        "List your skills (comma separated)",
        placeholder="e.g. Python, Machine Learning, SQL, React, Git, Docker...",
    )

    st.divider()

    # --- Achievements ---
    st.subheader("🏆 Achievements & Certifications")
    st.caption("Optional")
    achievements = st.text_area(
        "Certifications / Achievements / Extra-curriculars",
        placeholder="e.g. AWS Certified Cloud Practitioner, Winner of XYZ Hackathon...",
    )

    st.divider()

    # --- Target JD ---
    st.subheader("🎯 Target Job Description")
    st.caption("Optional but recommended for tailored results")
    jd_scratch = st.text_area(
        "Job Description", height=150,
        placeholder="Paste the JD to tailor your resume to a specific role...",
        label_visibility="collapsed",
    )
    if jd_scratch:
        st.caption(f"{len(jd_scratch):,} characters")

    g1, g2 = st.columns(2, gap="medium")
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
                st.subheader("Resume Preview")
                pdf_bytes = None
                try:
                    pdf_bytes = generate_pdf(resume, template2)
                    st.markdown(get_pdf_preview_html(pdf_bytes), unsafe_allow_html=True)
                except Exception as e:
                    logger.warning(f"PDF preview failed: {e}")
                    _show_resume(resume)

                # --- Download Actions ---
                st.divider()
                d1, d2, d3 = st.columns(3)
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
                    st.subheader("Cover Letter")
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
    st.markdown("Track every job application — company, role, status, and dates — all in one place.")

    st.divider()

    # --- Add New Application Form ---
    with st.form("add_app", clear_on_submit=True):
        st.subheader("➕ Add New Application")
        c1, c2, c3 = st.columns(3, gap="medium")
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
        st.subheader("📈 Overview")
        m1, m2, m3, m4 = st.columns(4)
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
                            "Applied": "#4f46e5",
                            "Interview Scheduled": "#2563eb",
                            "Under Review": "#d97706",
                            "Rejected": "#dc2626",
                            "Offer Received": "#16a34a",
                            "Accepted": "#059669",
                            "Withdrawn": "#94a3b8",
                        },
                    )
                    fig.update_layout(
                        showlegend=True,
                        legend=dict(orientation="h", y=-0.3, x=0.5, xanchor="center", font=dict(size=10)),
                        margin=dict(t=10, b=10, l=10, r=10),
                        height=300,
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                    )
                    fig.update_traces(textinfo="value", textfont_size=12)
                    st.plotly_chart(fig, use_container_width=True)
                except ImportError:
                    st.warning("Install `plotly` for chart visualization: `pip install plotly`")

        st.divider()

        # --- Filters ---
        st.subheader("🔍 Filter Applications")
        f1, f2, f3 = st.columns([2, 2, 1], gap="medium")
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

        st.markdown(f"**Applications ({len(filtered)} of {len(apps)})**")

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
                        st.markdown(f"{emoji} **{cs}**")

                    # Action row
                    a1, a2, a3 = st.columns([3, 1, 1])
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
    st.markdown("Browse all your previously generated and optimized resumes with quick download access.")

    st.divider()

    resumes = load_resumes()

    if resumes:
        st.metric("Total Resumes Saved", len(resumes))

        for i, entry in enumerate(resumes):
            mode = "Generated" if entry.get("mode") == "generated" else "Optimized"
            ts = entry.get("timestamp", "Unknown")
            cc = entry.get("char_count", len(entry.get("content", "")))
            mode_icon = "📝" if entry.get("mode") == "generated" else "🔧"

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

st.divider()
st.caption(
    "**AI Resume Generator** v2.0 · Built with Streamlit & Local AI · "
    "Resume analysis, optimization & career assistance — runs 100% on your machine."
)
