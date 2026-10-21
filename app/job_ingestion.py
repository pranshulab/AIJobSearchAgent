
from app.job_store import upsert_job


def normalize_job(raw: dict, source: str) -> dict:
    """Validate and normalize a job from an external source."""

    if not isinstance(raw, dict):
        raise ValueError("Each job must be a dictionary.")

    title = str(raw.get("title") or "").strip()
    company = str(raw.get("company") or "").strip()

    if not title:
        raise ValueError("Job title is required.")

    if not company:
        raise ValueError("Company name is required.")

    skills = raw.get("skills", [])

    if isinstance(skills, str):
        skills = [
            skill.strip()
            for skill in skills.split(",")
            if skill.strip()
        ]

    if not isinstance(skills, list):
        raise ValueError("Skills must be a list or comma-separated string.")

    skills = [
        str(skill).strip()
        for skill in skills
        if str(skill).strip()
    ]

    url = str(raw.get("url") or "").strip()

    if url and not url.startswith(("https://", "http://")):
        raise ValueError("Job URL must start with http:// or https://.")

    external_id = str(raw.get("external_id") or "").strip()

    return {
        "external_id": external_id,
        "source": source.strip(),
        "title": title,
        "company": company,
        "location": str(raw.get("location") or "").strip(),
        "description": str(raw.get("description") or "").strip(),
        "url": url,
        "skills": skills,
        "posted_at": str(raw.get("posted_at") or "").strip(),
    }


def ingest_jobs(
    records: list[dict],
    source: str,
    db_path=None,
) -> dict:
    """Validate and persist records, reporting successes and errors."""

    if not source or not source.strip():
        raise ValueError("Source name is required.")

    if not isinstance(records, list):
        raise ValueError("Jobs must be supplied as a list.")

    result = {
        "received": len(records),
        "inserted": 0,
        "updated": 0,
        "failed": 0,
        "errors": [],
    }

    for index, raw in enumerate(records):
        try:
            job = normalize_job(raw, source)

            if db_path is None:
                _, inserted = upsert_job(job)
            else:
                _, inserted = upsert_job(job, db_path=db_path)

            if inserted:
                result["inserted"] += 1
            else:
                result["updated"] += 1

        except (ValueError, TypeError, KeyError) as exc:
            result["failed"] += 1
            result["errors"].append({
                "index": index,
                "error": str(exc),
            })

    return result
