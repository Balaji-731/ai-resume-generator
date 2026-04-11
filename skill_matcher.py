"""
Skill Matcher — Extract and match skills using keyword-based analysis.
Supports category-wise breakdown and match scoring.
"""

import re
from dataclasses import dataclass, field

from config import SKILL_CATEGORIES, ALL_SKILLS
from logger import get_logger

logger = get_logger(__name__)


@dataclass
class SkillMatchResult:
    """Structured result of a skill matching operation."""
    matched: list = field(default_factory=list)
    missing: list = field(default_factory=list)
    score: float = 0.0
    category_breakdown: dict = field(default_factory=dict)


def extract_skills(text: str) -> list:
    """
    Extract recognized skills from text using keyword matching.

    Args:
        text: Input text (resume or job description).

    Returns:
        List of matched skill names (title-cased).
    """
    if not text or not text.strip():
        logger.warning("Empty text provided for skill extraction")
        return []

    text_lower = text.lower()
    found = set()

    for skill in ALL_SKILLS:
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower):
            found.add(skill.title())

    logger.info(f"Extracted {len(found)} skills from text ({len(text)} chars)")
    return sorted(found)


def extract_skills_by_category(text: str) -> dict:
    """
    Extract skills grouped by category.

    Args:
        text: Input text (resume or job description).

    Returns:
        Dictionary mapping category names to lists of matched skills.
    """
    if not text or not text.strip():
        return {}

    text_lower = text.lower()
    categorized = {}

    for category, skills in SKILL_CATEGORIES.items():
        matched = []
        for skill in skills:
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                matched.append(skill.title())
        if matched:
            categorized[category] = sorted(matched)

    return categorized


def match_skills(resume_skills: list, jd_skills: list) -> tuple:
    """
    Compare resume skills with job description skills.

    Args:
        resume_skills: Skills extracted from the resume.
        jd_skills: Skills extracted from the job description.

    Returns:
        Tuple of (matched_skills, missing_skills).
    """
    resume_lower = {s.lower() for s in resume_skills}

    matched = [s for s in jd_skills if s.lower() in resume_lower]
    missing = [s for s in jd_skills if s.lower() not in resume_lower]

    logger.info(f"Skill match: {len(matched)} matched, {len(missing)} missing out of {len(jd_skills)} JD skills")
    return matched, missing


def calculate_match_score(resume_text: str, jd_text: str) -> SkillMatchResult:
    """
    Perform a full skill match analysis between resume and job description.

    Args:
        resume_text: Full text of the resume.
        jd_text: Full text of the job description.

    Returns:
        SkillMatchResult with matched/missing skills, score, and category breakdown.
    """
    resume_skills = extract_skills(resume_text)
    jd_skills = extract_skills(jd_text)
    matched, missing = match_skills(resume_skills, jd_skills)

    total_jd = len(jd_skills)
    score = round((len(matched) / max(total_jd, 1)) * 100, 1)

    # Category-wise breakdown
    resume_by_cat = extract_skills_by_category(resume_text)
    jd_by_cat = extract_skills_by_category(jd_text)

    category_breakdown = {}
    for category in SKILL_CATEGORIES:
        r_skills = set(s.lower() for s in resume_by_cat.get(category, []))
        j_skills = jd_by_cat.get(category, [])
        if j_skills:
            cat_matched = [s for s in j_skills if s.lower() in r_skills]
            cat_missing = [s for s in j_skills if s.lower() not in r_skills]
            category_breakdown[category] = {
                "matched": cat_matched,
                "missing": cat_missing,
                "score": round((len(cat_matched) / max(len(j_skills), 1)) * 100, 1),
            }

    logger.info(f"Match score: {score}% — {len(matched)}/{total_jd} skills matched")

    return SkillMatchResult(
        matched=matched,
        missing=missing,
        score=score,
        category_breakdown=category_breakdown,
    )
