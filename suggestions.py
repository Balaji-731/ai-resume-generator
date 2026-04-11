"""
AI Improvement Suggestions — Analyze resume sections and provide actionable tips.
"""

from llm_helper import call_llm, LLMError
from logger import get_logger

logger = get_logger(__name__)


def generate_suggestions(resume_text: str, jd_text: str = "") -> str:
    """
    Generate section-by-section improvement suggestions for a resume.

    Args:
        resume_text: The resume text to analyze.
        jd_text: Optional job description for targeted suggestions.

    Returns:
        Formatted improvement suggestions as text.

    Raises:
        LLMError: If AI generation fails.
    """
    if not resume_text or not resume_text.strip():
        return "No resume text provided for analysis."

    logger.info(
        f"Generating suggestions — resume: {len(resume_text)} chars"
        + (f", JD: {len(jd_text)} chars" if jd_text else "")
    )

    jd_section = ""
    if jd_text and jd_text.strip():
        jd_section = f"""
TARGET JOB DESCRIPTION (use this to give role-specific suggestions):
---
{jd_text}
---"""

    prompt = f"""You are a resume review expert. Analyze the following resume and provide specific, actionable improvement suggestions.

RULES:
1. Analyze each section of the resume separately.
2. For each section, give 2-3 SHORT, specific tips (one sentence each).
3. Focus on: wording improvements, missing details, formatting suggestions, ATS compatibility.
4. Be constructive — point out what's good AND what can be improved.
5. Do NOT suggest adding fake content. Only suggest improving what exists or adding clearly missing standard elements.
6. Keep suggestions practical and immediately actionable.

Format your response EXACTLY like this:
CONTACT INFO:
+ [what's good]
- [what to improve]

PROFESSIONAL SUMMARY:
+ [what's good]
- [what to improve]

(continue for each section present in the resume)

OVERALL:
- [general tips]

RESUME TO ANALYZE:
---
{resume_text}
---
{jd_section}

Provide your analysis now. Be concise — maximum 2-3 tips per section."""

    result = call_llm(prompt)
    logger.info(f"Suggestions generated ({len(result)} chars)")
    return result
