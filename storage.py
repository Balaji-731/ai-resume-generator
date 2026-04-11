"""
Storage — Persistent data management for resumes and job applications.
Handles JSON and CSV storage with validation, thread safety, and CRUD operations.
"""

import json
import csv
import os
import threading
import pandas as pd
from datetime import datetime

from config import DATA_DIR, RESUMES_FILE, APPLICATIONS_FILE, APPLICATION_FIELDS
from logger import get_logger

logger = get_logger(__name__)

# Thread lock for file operations
_file_lock = threading.Lock()


def _ensure_data_dir() -> None:
    """Create the data directory if it doesn't exist."""
    os.makedirs(DATA_DIR, exist_ok=True)


# ─── Resume Storage ────────────────────────────────────────────────────────────

def save_resume(resume_text: str, mode: str = "generated") -> dict:
    """
    Save a resume to the JSON store.

    Args:
        resume_text: The resume text content.
        mode: Generation mode — 'generated' or 'optimized'.

    Returns:
        The saved resume entry dict.

    Raises:
        ValueError: If resume text is empty.
    """
    if not resume_text or not resume_text.strip():
        raise ValueError("Cannot save an empty resume.")

    _ensure_data_dir()

    with _file_lock:
        resumes = _load_resumes_raw()

        entry = {
            "id": len(resumes) + 1,
            "mode": mode,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "content": resume_text,
            "char_count": len(resume_text),
        }
        resumes.append(entry)

        with open(RESUMES_FILE, "w", encoding="utf-8") as f:
            json.dump(resumes, f, indent=2, ensure_ascii=False)

    logger.info(f"Resume saved — id: {entry['id']}, mode: {mode}, size: {len(resume_text)} chars")
    return entry


def load_resumes() -> list:
    """
    Load all saved resumes from the JSON store.

    Returns:
        List of resume entry dicts, newest first.
    """
    resumes = _load_resumes_raw()
    logger.info(f"Loaded {len(resumes)} saved resume(s)")
    return list(reversed(resumes))  # newest first


def _load_resumes_raw() -> list:
    """Load raw resume list from file."""
    if not os.path.exists(RESUMES_FILE):
        return []
    try:
        with open(RESUMES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"Failed to load resumes: {e}")
        return []


# ─── Application Storage ───────────────────────────────────────────────────────

def save_application(app: dict) -> None:
    """
    Save a job application entry to CSV.

    Args:
        app: Dictionary with application fields (company, role, date, status, link, notes).

    Raises:
        ValueError: If required fields (company, role) are missing.
    """
    if not app.get("company", "").strip():
        raise ValueError("Company name is required.")
    if not app.get("role", "").strip():
        raise ValueError("Job role is required.")

    _ensure_data_dir()

    with _file_lock:
        file_exists = os.path.exists(APPLICATIONS_FILE)
        with open(APPLICATIONS_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=APPLICATION_FIELDS)
            if not file_exists:
                writer.writeheader()
            # Ensure all fields exist with defaults
            row = {field: app.get(field, "") for field in APPLICATION_FIELDS}
            writer.writerow(row)

    logger.info(f"Application saved — {app.get('company')} / {app.get('role')}")


def load_applications() -> pd.DataFrame:
    """
    Load all job applications from CSV.

    Returns:
        DataFrame with application data, or empty DataFrame if no data.
    """
    if not os.path.exists(APPLICATIONS_FILE):
        return pd.DataFrame(columns=APPLICATION_FIELDS)
    try:
        df = pd.read_csv(APPLICATIONS_FILE, encoding="utf-8")
        logger.info(f"Loaded {len(df)} application(s)")
        return df
    except Exception as e:
        logger.error(f"Failed to load applications: {e}")
        return pd.DataFrame(columns=APPLICATION_FIELDS)


def update_application_status(index: int, new_status: str) -> bool:
    """
    Update the status of an application by its row index.

    Args:
        index: Row index (0-based) in the CSV.
        new_status: New status value.

    Returns:
        True if update succeeded, False otherwise.
    """
    try:
        df = load_applications()
        if index < 0 or index >= len(df):
            logger.warning(f"Invalid application index: {index}")
            return False

        df.at[index, "status"] = new_status
        with _file_lock:
            df.to_csv(APPLICATIONS_FILE, index=False, encoding="utf-8")

        logger.info(f"Application {index} status updated to: {new_status}")
        return True
    except Exception as e:
        logger.error(f"Failed to update application status: {e}")
        return False


def delete_application(index: int) -> bool:
    """
    Delete an application entry by its row index.

    Args:
        index: Row index (0-based) in the CSV.

    Returns:
        True if deletion succeeded, False otherwise.
    """
    try:
        df = load_applications()
        if index < 0 or index >= len(df):
            logger.warning(f"Invalid application index: {index}")
            return False

        df = df.drop(index).reset_index(drop=True)
        with _file_lock:
            df.to_csv(APPLICATIONS_FILE, index=False, encoding="utf-8")

        logger.info(f"Application {index} deleted")
        return True
    except Exception as e:
        logger.error(f"Failed to delete application: {e}")
        return False
