
import os

import requests


def fetch_authorized_jobs() -> list[dict]:
    """Fetch jobs from a configured, authorized JSON API.

    Expected response:
      - a JSON list of job objects, or
      - an object with a 'jobs' list.

    Provider-specific response formats must be mapped to this
    common format before ingestion.
    """

    api_url = os.getenv("JOB_API_URL", "").strip()

    if not api_url:
        raise RuntimeError(
            "JOB_API_URL is not configured. "
            "Set it to an authorized job API endpoint."
        )

    if not api_url.startswith("https://"):
        raise RuntimeError(
            "Configure a trusted HTTPS API endpoint."
        )

    headers = {
        "Accept": "application/json",
        "User-Agent": "AIJobSearchAgent/0.1",
    }

    api_key = os.getenv("JOB_API_KEY", "").strip()

    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        response = requests.get(
            api_url,
            headers=headers,
            timeout=(5, 20),
        )
        response.raise_for_status()
        payload = response.json()

    except requests.RequestException as exc:
        raise RuntimeError(
            f"Job API request failed: {exc}"
        ) from exc

    except ValueError as exc:
        raise RuntimeError(
            "Job API returned invalid JSON."
        ) from exc

    if isinstance(payload, dict):
        payload = payload.get("jobs")

    if not isinstance(payload, list):
        raise RuntimeError(
            "Expected a JSON list of jobs or an object with a 'jobs' list."
        )

    if not all(isinstance(item, dict) for item in payload):
        raise RuntimeError(
            "The API response contains a non-object job record."
        )

    return payload
