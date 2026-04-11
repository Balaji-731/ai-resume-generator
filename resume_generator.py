"""
Resume Generator — Generate professional resumes from scratch.
"""

from llm_helper import call_llm, LLMError
from logger import get_logger

logger = get_logger(__name__)

REQUIRED_FIELDS = ["name", "email", "degree", "college"]


def validate_user_data(user_data: dict) -> list:
    """
    Validate that required fields are present in user data.

    Args:
        user_data: Dictionary of user-provided information.

    Returns:
        List of missing required field names (empty if all present).
    """
    missing = []
    for field in REQUIRED_FIELDS:
        value = user_data.get(field, "")
        if not value or not str(value).strip():
            missing.append(field.replace("_", " ").title())
    return missing


def generate_resume_from_scratch(user_data: dict) -> str:
    """
    Generate a complete professional resume from user-provided data.

    Args:
        user_data: Dictionary containing personal info, education, skills, etc.

    Returns:
        Generated resume text.

    Raises:
        ValueError: If required fields are missing.
        LLMError: If AI generation fails.
    """
    missing = validate_user_data(user_data)
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")

    logger.info(f"Generating resume from scratch for: {user_data.get('name', 'Unknown')}")

    # Build sections only from provided data
    sections = []
    sections.append(f"Full Name: {user_data.get('name', '')}")
    sections.append(f"Email: {user_data.get('email', '')}")

    if user_data.get('phone', '').strip():
        sections.append(f"Phone: {user_data['phone']}")
    if user_data.get('location', '').strip():
        sections.append(f"Location: {user_data['location']}")
    if user_data.get('linkedin', '').strip():
        sections.append(f"LinkedIn: {user_data['linkedin']}")
    if user_data.get('github', '').strip():
        sections.append(f"GitHub: {user_data['github']}")

    sections.append(f"\nDegree: {user_data.get('degree', '')}")
    sections.append(f"College/University: {user_data.get('college', '')}")
    if user_data.get('grad_year', '').strip():
        sections.append(f"Graduation Year: {user_data['grad_year']}")
    if user_data.get('cgpa', '').strip():
        sections.append(f"CGPA/Percentage: {user_data['cgpa']}")

    if user_data.get('experience', '').strip():
        sections.append(f"\nEXPERIENCE/INTERNSHIPS:\n{user_data['experience']}")

    if user_data.get('projects', '').strip():
        sections.append(f"\nPROJECTS:\n{user_data['projects']}")

    if user_data.get('skills', '').strip():
        sections.append(f"\nSKILLS:\n{user_data['skills']}")

    if user_data.get('achievements', '').strip():
        sections.append(f"\nACHIEVEMENTS & CERTIFICATIONS:\n{user_data['achievements']}")

    user_info = "\n".join(sections)

    # Build job description section if provided
    jd_section = ""
    if user_data.get("job_description", "").strip():
        jd_section = f"""
TARGET JOB DESCRIPTION (use this ONLY to reorder skills and adjust the summary tone — do NOT invent experience or skills to match):
---
{user_data['job_description']}
---"""

    prompt = f"""You are a resume formatting assistant. Your ONLY job is to take the user's EXACT information below and format it into a clean, professional, ATS-friendly resume.

STRICT RULES — YOU MUST FOLLOW ALL OF THESE:
1. Use ONLY the information provided below. Do NOT invent, fabricate, or assume ANY details.
2. If a section (experience, projects, achievements) is NOT provided below, do NOT include that section at all. Simply skip it.
3. Do NOT add fake company names, fake project names, fake metrics, fake percentages, or fake achievements.
4. Do NOT add skills that the user did not list.
5. You MAY improve the WORDING of what the user provided — use professional language, strong action verbs, and clean phrasing.
6. You MAY write a short Professional Summary (2-3 lines) but it must ONLY reference skills and experience the user actually provided.
7. Keep the exact same facts — only polish the language and structure.
8. Format: plain text, no tables, no graphics, no columns. Use clear section headers and bullet points.
9. If the user has no experience, do NOT create fake experience. Instead, emphasize their projects, skills, and education.

USER'S INFORMATION (use ONLY this data):
===
{user_info}
===
{jd_section}

OUTPUT: Write ONLY the formatted resume in clean plain text. No commentary, no notes, no explanations."""

    result = call_llm(prompt)
    logger.info(f"Resume generated successfully ({len(result)} chars)")
    return result
