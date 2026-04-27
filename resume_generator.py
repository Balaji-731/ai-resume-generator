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

    prompt = f"""You are a senior resume formatting and ATS optimization engine. Your ONLY job is to take the user's EXACT information below and produce a clean, professional, industry-level resume suitable for AI/ML roles.

STRICT RULES — YOU MUST FOLLOW ALL OF THESE:

1. STRUCTURE (follow this exact order):
   - Full Name (first line, standalone)
   - Contact line: Email | Phone | Location | LinkedIn URL | GitHub URL (all on one line, separated by |)
   - PROFESSIONAL SUMMARY (2-3 concise lines)
   - TECHNICAL SKILLS
   - EXPERIENCE (if provided)
   - PROJECTS (if provided)
   - EDUCATION
   - CERTIFICATIONS (only if provided)
   - ACHIEVEMENTS (only if provided)

2. CONTENT RULES:
   - Use ONLY the information provided below. Do NOT invent, fabricate, or assume ANY details.
   - If a section is NOT provided, do NOT include it. Simply skip it.
   - Do NOT add fake company names, project names, metrics, percentages, or achievements.
   - Do NOT add skills the user did not list.
   - You MAY improve WORDING — use professional language, strong action verbs (Built, Developed, Deployed, Optimized, Designed), and clean phrasing.
   - You MAY write a short Professional Summary (2-3 lines) but it must ONLY reference skills and experience the user actually provided.

3. SKILLS SECTION:
   - Group into categories on separate lines:
     Machine Learning & AI: (relevant skills)
     Backend & Deployment: (relevant skills)
     Programming Languages: (relevant skills)
   - If a category has no matching skills from the user's list, omit that category.
   - Avoid duplicate or vague entries.

4. EXPERIENCE & PROJECT BULLETS:
   - Keep each bullet to 1-2 lines maximum.
   - Start with action verbs: Built, Developed, Deployed, Optimized, Designed, Implemented, Engineered.
   - Limit each project to 3-4 strong bullet points.
   - Mention: problem solved, technologies used, and impact/result.

5. EDUCATION:
   - Format: Degree — University Name | Year | CGPA (if provided)
   - Clean single block.

6. FORMATTING RULES:
   - Use consistent bullet style (- only).
   - Plain text only — no tables, no graphics, no columns, no markdown bold/italic.
   - No duplicate headings or content.
   - Remove empty sections automatically.
   - No broken words or line splits.
   - Strictly 1 page worth of content — prioritize most important content only.

7. If the user has no experience, do NOT create fake experience. Instead, emphasize projects, skills, and education.

USER'S INFORMATION (use ONLY this data):
===
{user_info}
===
{jd_section}

OUTPUT: Write ONLY the formatted resume in clean plain text. No commentary, no notes, no explanations."""

    result = call_llm(prompt)
    logger.info(f"Resume generated successfully ({len(result)} chars)")
    return result
