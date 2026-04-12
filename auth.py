"""
Auth — Authentication module using Supabase Auth.
Handles sign-up, sign-in, sign-out, and session management.
"""

import streamlit as st
from supabase_client import get_supabase
from logger import get_logger

logger = get_logger(__name__)


def sign_up(email: str, password: str, name: str = "") -> dict:
    """
    Register a new user with Supabase Auth, then auto sign-in.

    Args:
        email: User's email address.
        password: User's password (min 6 chars, enforced by Supabase).
        name: User's display name (stored in user metadata).

    Returns:
        Dict with 'success' (bool), 'user' (dict or None), 'error' (str or None).
    """
    if not email or not email.strip():
        return {"success": False, "user": None, "error": "Email is required."}
    if not password or len(password) < 6:
        return {"success": False, "user": None, "error": "Password must be at least 6 characters."}

    try:
        supabase = get_supabase()
        response = supabase.auth.sign_up({
            "email": email.strip(),
            "password": password,
            "options": {
                "data": {"name": name.strip()} if name else {}
            }
        })

        if not response.user:
            return {"success": False, "user": None, "error": "Sign-up failed. Please try again."}

        logger.info(f"User registered: {email}")

        # If Supabase returned a session (email confirm disabled), use it directly
        if response.session:
            user_data = _build_user_data(response.user, name)
            return {"success": True, "user": user_data, "error": None}

        # If no session (email confirm enabled), try to sign in immediately
        # This works if user auto-confirmed or confirm is off at Supabase level
        try:
            signin_resp = supabase.auth.sign_in_with_password({
                "email": email.strip(),
                "password": password,
            })
            if signin_resp.user and signin_resp.session:
                user_data = _build_user_data(signin_resp.user, name)
                logger.info(f"Auto sign-in after registration: {email}")
                return {"success": True, "user": user_data, "error": None}
        except Exception as signin_err:
            logger.warning(f"Auto sign-in failed (email confirmation may be required): {signin_err}")

        # Fallback: registration succeeded but can't auto-login
        # Still return success with user data (RLS won't work but basic app access will)
        user_data = _build_user_data(response.user, name)
        return {"success": True, "user": user_data, "error": None}

    except Exception as e:
        error_msg = str(e)
        if "already registered" in error_msg.lower() or "already been registered" in error_msg.lower():
            return {"success": False, "user": None, "error": "This email is already registered. Please sign in."}
        logger.error(f"Sign-up error: {e}")
        return {"success": False, "user": None, "error": f"Sign-up failed: {error_msg}"}


def sign_in(email: str, password: str) -> dict:
    """
    Authenticate an existing user with Supabase Auth.

    Args:
        email: User's email address.
        password: User's password.

    Returns:
        Dict with 'success' (bool), 'user' (dict or None), 'error' (str or None).
    """
    if not email or not email.strip():
        return {"success": False, "user": None, "error": "Email is required."}
    if not password:
        return {"success": False, "user": None, "error": "Password is required."}

    try:
        supabase = get_supabase()
        response = supabase.auth.sign_in_with_password({
            "email": email.strip(),
            "password": password,
        })

        if response.user:
            metadata = response.user.user_metadata or {}
            user_data = {
                "id": str(response.user.id),
                "email": response.user.email,
                "name": metadata.get("name", response.user.email.split("@")[0]),
            }
            logger.info(f"User signed in: {email}")
            return {"success": True, "user": user_data, "error": None}
        else:
            return {"success": False, "user": None, "error": "Invalid email or password."}

    except Exception as e:
        error_msg = str(e)
        if "invalid" in error_msg.lower() or "credentials" in error_msg.lower():
            return {"success": False, "user": None, "error": "Invalid email or password."}
        if "email not confirmed" in error_msg.lower():
            return {"success": False, "user": None, "error": "Please confirm your email before signing in. Check your inbox."}
        logger.error(f"Sign-in error: {e}")
        return {"success": False, "user": None, "error": f"Sign-in failed: {error_msg}"}


def sign_out() -> None:
    """Sign out the current user and clear session state."""
    try:
        supabase = get_supabase()
        supabase.auth.sign_out()
    except Exception as e:
        logger.warning(f"Sign-out API call failed (non-critical): {e}")

    # Clear all auth-related session state
    for key in ["current_user", "auth_token"]:
        st.session_state.pop(key, None)
    logger.info("User signed out")


def get_current_user() -> dict | None:
    """
    Get the currently logged-in user from session state.

    Returns:
        User dict with 'id', 'email', 'name' — or None if not logged in.
    """
    return st.session_state.get("current_user", None)


def is_authenticated() -> bool:
    """Check if a user is currently logged in."""
    return get_current_user() is not None


def _build_user_data(user, name: str = "") -> dict:
    """Build a standardized user data dict from a Supabase user object."""
    metadata = user.user_metadata or {}
    return {
        "id": str(user.id),
        "email": user.email,
        "name": name.strip() or metadata.get("name", user.email.split("@")[0]),
    }
