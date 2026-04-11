"""
Cover Letter Generator — Generate job-aligned cover letters using AI.
"""

from llm_helper import call_llm, LLMError
from logger import get_logger

logger = get_logger(__name__)


def generate_cover_letter(resume_text: str, job_description: str) -> str:
    """
    Generate a professional cover letter based on resume and job description.

    Args:
        resume_text: The resume text content.
        job_description: The target job description.

    Returns:
        Generated cover letter text.

    Raises:
        ValueError: If inputs are empty or invalid.
        LLMError: If AI generation fails.
    """
    if not resume_text or not resume_text.strip():
        raise ValueError("Resume text cannot be empty for cover letter generation.")
    if not job_description or not job_description.strip():
        raise ValueError("Job description is required for cover letter generation.")

    logger.info(
        f"Generating cover letter — resume: {len(resume_text)} chars, "
        f"JD: {len(job_description)} chars"
    )

    prompt = f"""You are a professional cover letter writer. Write a cover letter based STRICTLY on the resume and job description below.

STRICT RULES — YOU MUST FOLLOW ALL OF THESE:
1. Reference ONLY skills, experiences, projects, and achievements that are actually mentioned in the resume below.
2. Do NOT invent any accomplishments, metrics, company names, or experiences not present in the resume.
3. Do NOT fabricate quantified results (percentages, numbers, team sizes) that are not in the resume.
4. You MAY rephrase and present the resume content in a compelling narrative form.
5. Keep it to 3-4 paragraphs, approximately 250-350 words.
6. Opening: Express interest in the specific role described in the JD.
7. Body: Connect 2-3 real skills/experiences from the resume to key JD requirements.
8. Closing: Express eagerness for an interview and thank the reader.
9. Use formal letter format with "Dear Hiring Manager," and "Sincerely," closing.
10. Include the candidate's name at the end (from the resume).

RESUME (use ONLY facts from this):
---
{resume_text}
---

JOB DESCRIPTION (match the tone and role — but do NOT invent experience to fit):
---
{job_description}
---

OUTPUT: Write ONLY the cover letter. No commentary, no notes."""

    result = call_llm(prompt)
    logger.info(f"Cover letter generated successfully ({len(result)} chars)")
    return result
