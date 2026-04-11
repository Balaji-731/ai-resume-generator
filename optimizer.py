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

    prompt = f"""You are a resume formatting and polishing assistant. Your job is to improve the WORDING and STRUCTURE of the resume below to better match the job description. 

STRICT RULES — YOU MUST FOLLOW ALL OF THESE:
1. Use ONLY the information already present in the original resume. Do NOT invent new experiences, projects, companies, or achievements.
2. Do NOT fabricate metrics, percentages, team sizes, or quantified results that are not in the original resume.
3. Do NOT add skills that are not already mentioned or clearly implied in the original resume.
4. You MAY rewrite bullet points with stronger action verbs and more professional phrasing.
5. You MAY reorder sections and skills to better align with the job description.
6. You MAY improve the Professional Summary to better highlight relevant existing skills for the target role.
7. You MAY remove irrelevant information that doesn't serve the target role.
8. Keep all facts, dates, company names, and project details EXACTLY as they appear in the original.
9. Format: plain text, ATS-friendly — no tables, no graphics, no columns.
10. Structure: Contact Info → Professional Summary → Skills → Experience → Education → Projects → Certifications.

ORIGINAL RESUME (preserve all facts from this):
---
{resume_text}
---

TARGET JOB DESCRIPTION (use this to guide wording and ordering — NOT to invent new content):
---
{job_description}
---

OUTPUT: Write the complete polished resume in clean plain text. No commentary, no notes — only the resume."""

    result = call_llm(prompt)
    logger.info(f"Resume optimized successfully ({len(result)} chars)")
    return result
