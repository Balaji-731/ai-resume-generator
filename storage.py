"""
Storage — Cloud data management using Supabase PostgreSQL.
Handles resume and job application CRUD with per-user data isolation.
"""

import pandas as pd
from datetime import datetime

from supabase_client import get_supabase
from config import APPLICATION_FIELDS
from logger import get_logger

logger = get_logger(__name__)


# ─── Resume Storage ────────────────────────────────────────────────────────────

def save_resume(resume_text: str, mode: str = "generated", user_id: str = None) -> dict:
    """
    Save a resume to the Supabase resumes table.

    Args:
        resume_text: The resume text content.
        mode: Generation mode — 'generated' or 'optimized'.
        user_id: The authenticated user's UUID.

    Returns:
        The saved resume entry dict.

    Raises:
        ValueError: If resume text is empty or user_id is missing.
    """
    if not resume_text or not resume_text.strip():
        raise ValueError("Cannot save an empty resume.")
    if not user_id:
        raise ValueError("User ID is required to save a resume.")

    try:
        supabase = get_supabase()
        entry = {
            "user_id": user_id,
            "mode": mode,
            "content": resume_text,
            "char_count": len(resume_text),
        }
        response = supabase.table("resumes").insert(entry).execute()

        logger.info(f"Resume saved — user: {user_id}, mode: {mode}, size: {len(resume_text)} chars")
        return response.data[0] if response.data else entry

    except Exception as e:
        logger.error(f"Failed to save resume: {e}")
        raise


def load_resumes(user_id: str = None) -> list:
    """
    Load all saved resumes for a user from Supabase.

    Args:
        user_id: The authenticated user's UUID.

    Returns:
        List of resume entry dicts, newest first.
    """
    if not user_id:
        return []

    try:
        supabase = get_supabase()
        response = (
            supabase.table("resumes")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        resumes = response.data or []
        logger.info(f"Loaded {len(resumes)} resume(s) for user {user_id}")

        # Map 'created_at' to 'timestamp' for backward compatibility with UI
        for r in resumes:
            r["timestamp"] = r.get("created_at", "Unknown")

        return resumes

    except Exception as e:
        logger.error(f"Failed to load resumes: {e}")
        return []


# ─── Application Storage ───────────────────────────────────────────────────────

def save_application(app: dict, user_id: str = None) -> None:
    """
    Save a job application entry to Supabase.

    Args:
        app: Dictionary with application fields (company, role, date, status, link, notes).
        user_id: The authenticated user's UUID.

    Raises:
        ValueError: If required fields (company, role) or user_id are missing.
    """
    if not app.get("company", "").strip():
        raise ValueError("Company name is required.")
    if not app.get("role", "").strip():
        raise ValueError("Job role is required.")
    if not user_id:
        raise ValueError("User ID is required to save an application.")

    try:
        supabase = get_supabase()
        entry = {
            "user_id": user_id,
            "company": app.get("company", ""),
            "role": app.get("role", ""),
            "date": app.get("date", ""),
            "status": app.get("status", "Applied"),
            "link": app.get("link", ""),
            "notes": app.get("notes", ""),
        }
        supabase.table("applications").insert(entry).execute()
        logger.info(f"Application saved — {app.get('company')} / {app.get('role')}")

    except Exception as e:
        logger.error(f"Failed to save application: {e}")
        raise


def load_applications(user_id: str = None) -> pd.DataFrame:
    """
    Load all job applications for a user from Supabase.

    Args:
        user_id: The authenticated user's UUID.

    Returns:
        DataFrame with application data, or empty DataFrame if no data.
    """
    if not user_id:
        return pd.DataFrame(columns=APPLICATION_FIELDS)

    try:
        supabase = get_supabase()
        response = (
            supabase.table("applications")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        data = response.data or []
        if data:
            df = pd.DataFrame(data)
            logger.info(f"Loaded {len(df)} application(s) for user {user_id}")
            return df
        else:
            return pd.DataFrame(columns=APPLICATION_FIELDS)

    except Exception as e:
        logger.error(f"Failed to load applications: {e}")
        return pd.DataFrame(columns=APPLICATION_FIELDS)


def update_application_status(app_id: int, new_status: str) -> bool:
    """
    Update the status of an application by its database ID.

    Args:
        app_id: The application row ID in Supabase.
        new_status: New status value.

    Returns:
        True if update succeeded, False otherwise.
    """
    try:
        supabase = get_supabase()
        response = (
            supabase.table("applications")
            .update({"status": new_status})
            .eq("id", app_id)
            .execute()
        )
        if response.data:
            logger.info(f"Application {app_id} status updated to: {new_status}")
            return True
        else:
            logger.warning(f"No application found with id: {app_id}")
            return False

    except Exception as e:
        logger.error(f"Failed to update application status: {e}")
        return False


def delete_application(app_id: int) -> bool:
    """
    Delete an application entry by its database ID.

    Args:
        app_id: The application row ID in Supabase.

    Returns:
        True if deletion succeeded, False otherwise.
    """
    try:
        supabase = get_supabase()
        response = (
            supabase.table("applications")
            .delete()
            .eq("id", app_id)
            .execute()
        )
        if response.data:
            logger.info(f"Application {app_id} deleted")
            return True
        else:
            logger.warning(f"No application found with id: {app_id}")
            return False

    except Exception as e:
        logger.error(f"Failed to delete application: {e}")
        return False
