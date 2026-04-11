"""
LLM Helper — Ollama (Local LLM) integration.
Provides reliable LLM calls with retry logic, response validation, and logging.
All data stays on your machine — no external API calls.
"""

import time
import requests

from config import (
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
    LLM_MAX_RETRIES,
    LLM_RETRY_DELAY,
)
from logger import get_logger

logger = get_logger(__name__)


class LLMError(Exception):
    """Custom exception for LLM-related errors."""
    pass


def check_ollama_connection() -> bool:
    """
    Check if Ollama server is running and accessible.

    Returns:
        True if Ollama is reachable, False otherwise.
    """
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        return response.status_code == 200
    except requests.ConnectionError:
        return False
    except Exception:
        return False


def get_available_models() -> list:
    """
    Get the list of models available in Ollama.

    Returns:
        List of model name strings.
    """
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
    except Exception:
        pass
    return []


def call_llm(prompt: str, temperature: float = None) -> str:
    """
    Call the local Ollama LLM with retry logic and response validation.

    Args:
        prompt: The text prompt to send to the model.
        temperature: Override default temperature if needed.

    Returns:
        Generated text response from the local LLM.

    Raises:
        LLMError: If all retries fail or Ollama is not running.
    """
    # Check if Ollama is running
    if not check_ollama_connection():
        raise LLMError(
            "Cannot connect to Ollama. Make sure Ollama is running.\n"
            "Start it with: ollama serve\n"
            f"Expected at: {OLLAMA_BASE_URL}"
        )

    url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature or LLM_TEMPERATURE,
            "num_predict": LLM_MAX_TOKENS,
        },
    }

    last_error = None
    for attempt in range(1, LLM_MAX_RETRIES + 1):
        try:
            logger.info(f"Ollama API call — attempt {attempt}/{LLM_MAX_RETRIES} (model: {OLLAMA_MODEL})")
            response = requests.post(url, json=payload, timeout=120)

            if response.status_code != 200:
                error_detail = response.text[:200] if response.text else "No details"
                raise LLMError(f"Ollama returned status {response.status_code}: {error_detail}")

            data = response.json()
            text = data.get("response", "").strip()

            if not text:
                raise LLMError("Empty response received from Ollama.")

            if len(text) < 10:
                raise LLMError("Response too short — likely an error.")

            logger.info(f"Ollama call successful (response: {len(text)} chars)")
            return text

        except LLMError:
            raise
        except requests.ConnectionError:
            last_error = "Connection lost to Ollama server."
            logger.warning(f"Attempt {attempt} failed: Connection error")
        except requests.Timeout:
            last_error = "Request timed out. The model may be loading or the prompt is too long."
            logger.warning(f"Attempt {attempt} failed: Timeout")
        except Exception as e:
            last_error = e
            logger.warning(f"Attempt {attempt} failed: {type(e).__name__}: {e}")

        if attempt < LLM_MAX_RETRIES:
            wait = LLM_RETRY_DELAY * (2 ** (attempt - 1))
            logger.info(f"Retrying in {wait}s...")
            time.sleep(wait)

    error_msg = f"All {LLM_MAX_RETRIES} attempts failed. Last error: {last_error}"
    logger.error(error_msg)
    raise LLMError(error_msg)
