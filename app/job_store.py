
import hashlib
import json
import re
import sqlite3
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


DEFAULT_DB_PATH = Path("data/jobs.db")


def _connect(db_path=DEFAULT_DB_PATH):
    """Open a SQLite connection and enable foreign-key enforcement."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(str(path), timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def normalize_url(url: str) -> str:
    """Normalize URLs for duplicate detection.

    Removes query parameters and fragments to reduce duplicates
    caused by tracking links.
    """
    if not url:
        return ""

    parts = urlsplit(url.strip())

    if parts.scheme.lower() not in {"http", "https"} or not parts.netloc:
        return ""

    return urlunsplit((
        parts.scheme.lower(),
        parts.netloc.lower(),
        parts.path.rstrip("/"),
        "",
        "",
    ))


def make_dedupe_key(job: dict) -> str:
    """Create a stable key using the URL, source ID, or job details."""
    normalized_url = normalize_url(job.get("url", ""))

    if normalized_url:
        identity = f"url:{normalized_url}"
    elif job.get("external_id"):
        identity = (
            f"id:{job.get('source', '').casefold()}:"
            f"{job['external_id'].strip()}"
        )
    else:
        identity = "|".join([
            job.get("title", "").strip().casefold(),
            job.get("company", "").strip().casefold(),
            job.get("location", "").strip().casefold(),
        ])

    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def init_db(db_path=DEFAULT_DB_PATH):
    """Create the jobs table and indexes if they don't exist."""
    with _connect(db_path) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                external_id TEXT,
                source TEXT NOT NULL,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                location TEXT NOT NULL DEFAULT '',
                description TEXT NOT NULL DEFAULT '',
                url TEXT NOT NULL DEFAULT '',
                skills_json TEXT NOT NULL DEFAULT '[]',
                posted_at TEXT NOT NULL DEFAULT '',
                dedupe_key TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_jobs_company
            ON jobs(company)
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_jobs_created_at
            ON jobs(created_at)
        """)


def upsert_job(job: dict, db_path=DEFAULT_DB_PATH) -> tuple[int, bool]:
    """Insert a job or refresh an existing duplicate.

    Returns:
        (database_id, inserted)
        inserted is True for a new job and False for a duplicate.
    """
    init_db(db_path)

    dedupe_key = make_dedupe_key(job)

    values = (
        job.get("external_id") or None,
        job["source"].strip(),
        job["title"].strip(),
        job["company"].strip(),
        job.get("location", "").strip(),
        job.get("description", "").strip(),
        normalize_url(job.get("url", "")),
        json.dumps(job.get("skills", [])),
        job.get("posted_at", "").strip(),
        dedupe_key,
    )

    with _connect(db_path) as connection:
        existing = connection.execute(
            "SELECT id FROM jobs WHERE dedupe_key = ?",
            (dedupe_key,),
        ).fetchone()

        if existing:
            connection.execute("""
                UPDATE jobs
                SET external_id = ?,
                    source = ?,
                    title = ?,
                    company = ?,
                    location = ?,
                    description = ?,
                    url = ?,
                    skills_json = ?,
                    posted_at = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, values[:9] + (existing["id"],))

            return existing["id"], False

        cursor = connection.execute("""
            INSERT INTO jobs (
                external_id, source, title, company, location,
                description, url, skills_json, posted_at, dedupe_key
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, values)

        return cursor.lastrowid, True


def list_jobs(db_path=DEFAULT_DB_PATH) -> list[dict]:
    """Return stored jobs in newest-first order."""
    init_db(db_path)

    with _connect(db_path) as connection:
        rows = connection.execute("""
            SELECT * FROM jobs
            ORDER BY created_at DESC, id DESC
        """).fetchall()

    jobs = []

    for row in rows:
        job = dict(row)
        job["skills"] = json.loads(job.pop("skills_json"))
        jobs.append(job)

    return jobs


def count_jobs(db_path=DEFAULT_DB_PATH) -> int:
    """Return the total number of distinct stored jobs."""
    init_db(db_path)

    with _connect(db_path) as connection:
        return connection.execute(
            "SELECT COUNT(*) FROM jobs"
        ).fetchone()[0]
