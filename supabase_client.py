"""
Supabase Client — Singleton client for Supabase API access.
Reads credentials from Streamlit secrets (.streamlit/secrets.toml).
"""

import streamlit as st
from supabase import create_client, Client
from logger import get_logger

logger = get_logger(__name__)

_client: Client | None = None


def get_supabase() -> Client:
    """
    Get (or create) the Supabase client singleton.

    Returns:
        Supabase Client instance.

    Raises:
        RuntimeError: If SUPABASE_URL or SUPABASE_KEY are not set in secrets.
    """
    global _client
    if _client is not None:
        return _client

    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY")

    if not url or not key:
        raise RuntimeError(
            "Supabase credentials not found. "
            "Add SUPABASE_URL and SUPABASE_KEY to .streamlit/secrets.toml"
        )

    _client = create_client(url, key)
    logger.info("Supabase client initialized successfully")
    return _client
