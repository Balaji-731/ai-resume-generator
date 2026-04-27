"""
Resume Optimizer — Optimize existing resumes for specific job descriptions.
"""

from llm_helper import call_llm, LLMError
from logger import get_logger

logger = get_logger(__name__)


def optimize_resume(resume_text: str, job_description: str) -> str:
    """
    Optimize an existing resume for a specific job description using AI.

    Args:
        resume_text: The original resume text content.
        job_description: The target job description.

    Returns:
        Optimized resume text.

    Raises:
        ValueError: If inputs are empty or invalid.
        LLMError: If AI generation fails.
    """
    if not resume_text or not resume_text.strip():
        raise ValueError("Resume text cannot be empty.")
    if not job_description or not job_description.strip():
        raise ValueError("Job description cannot be empty.")

    logger.info(
        f"Optimizing resume ({len(resume_text)} chars) "
        f"for job description ({len(job_description)} chars)"
    )

    prompt = f"""You are a senior resume formatting and ATS optimization engine. Rewrite and restructure the resume below into a clean, professional, industry-level layout optimized for the target job description.

STRICT RULES — YOU MUST FOLLOW ALL OF THESE:

1. STRUCTURE (follow this exact order):
   - Full Name (first line, standalone, large emphasis)
   - Contact line: Email | Phone | Location | LinkedIn URL | GitHub URL (all on one line, separated by |)
   - PROFESSIONAL SUMMARY (2-3 concise, impactful lines tailored to the job)
   - TECHNICAL SKILLS (grouped by category)
   - EXPERIENCE (if present in original)
   - PROJECTS (if present in original)
   - EDUCATION
   - CERTIFICATIONS (only if present in original)
   - ACHIEVEMENTS (only if present in original)

2. CONTENT RULES:
   - Use ONLY the information already present in the original resume. Do NOT invent new experiences, projects, companies, or achievements.
   - Do NOT fabricate metrics, percentages, team sizes, or quantified results not in the original.
   - Do NOT add skills not already mentioned or clearly implied.
   - You MAY rewrite bullet points with stronger action verbs (Built, Developed, Deployed, Optimized, Designed, Implemented, Engineered) and more professional phrasing.
   - You MAY reorder sections and skills to better align with the job description.
   - You MAY improve the Professional Summary to better highlight relevant existing skills.
   - You MAY remove irrelevant information that doesn't serve the target role.
   - Keep all facts, dates, company names, and project details EXACTLY as they appear.

3. SKILLS SECTION:
   - Group into categories on separate lines:
     Machine Learning & AI: (relevant skills)
     Backend & Deployment: (relevant skills)
     Programming Languages: (relevant skills)
   - Order skills by relevance to the target job description.
   - If a category has no matching skills, omit that category.
   - Avoid duplicate or vague entries.

4. EXPERIENCE & PROJECT BULLETS:
   - Rewrite to be concise, impactful, and achievement-focused.
   - Each bullet: 1-2 lines maximum.
   - Start with action verbs.
   - Limit each project/role to 3-4 strong bullets.
   - Mention: problem solved, technologies used, impact/result.
   - Remove redundancy and repetition.

5. EDUCATION:
   - Format: Degree — University Name | Year | CGPA (if present)
   - Clean single block.

6. FORMATTING RULES:
   - Use consistent bullet style (- only).
   - Plain text only — no tables, no graphics, no columns, no markdown bold/italic.
   - No duplicate headings or content.
   - Remove empty sections automatically.
   - No broken words or line splits.
   - Strictly 1 page worth of content — prioritize most important content only.
   - Maintain equal spacing between sections.

ORIGINAL RESUME (preserve all facts from this):
---
{resume_text}
---

TARGET JOB DESCRIPTION (use this to guide wording, ordering, and emphasis — NOT to invent new content):
---
{job_description}
---

OUTPUT: Write the complete polished resume in clean plain text. No commentary, no notes — only the resume."""

    result = call_llm(prompt)
    logger.info(f"Resume optimized successfully ({len(result)} chars)")
    return result
