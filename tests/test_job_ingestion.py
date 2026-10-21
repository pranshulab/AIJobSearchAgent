
import pytest

from app.job_ingestion import ingest_jobs, normalize_job
from app.job_store import count_jobs


def sample_job():
    return {
        "external_id": "job-1",
        "title": "Python Engineer",
        "company": "Example Company",
        "location": "India",
        "description": "Develop Python services.",
        "url": "https://example.com/jobs/job-1",
        "skills": ["Python", "SQL"],
    }


def test_normalize_job():
    result = normalize_job(sample_job(), "test-api")

    assert result["source"] == "test-api"
    assert result["title"] == "Python Engineer"
    assert result["skills"] == ["Python", "SQL"]


def test_normalize_comma_separated_skills():
    raw = sample_job()
    raw["skills"] = "Python, SQL, RAG"

    result = normalize_job(raw, "test-api")

    assert result["skills"] == ["Python", "SQL", "RAG"]


def test_missing_title_is_rejected():
    raw = sample_job()
    raw["title"] = ""

    with pytest.raises(ValueError, match="title"):
        normalize_job(raw, "test-api")


def test_invalid_url_is_rejected():
    raw = sample_job()
    raw["url"] = "javascript:alert(1)"

    with pytest.raises(ValueError, match="URL"):
        normalize_job(raw, "test-api")


def test_ingestion_counts_new_and_duplicate_jobs(tmp_path):
    db_path = tmp_path / "test.db"
    first = sample_job()
    second = sample_job()

    result = ingest_jobs(
        [first, second],
        source="test-api",
        db_path=db_path,
    )

    assert result["received"] == 2
    assert result["inserted"] == 1
    assert result["updated"] == 1
    assert result["failed"] == 0
    assert count_jobs(db_path) == 1


def test_ingestion_continues_after_invalid_record(tmp_path):
    db_path = tmp_path / "test.db"

    invalid = sample_job()
    invalid["company"] = ""

    result = ingest_jobs(
        [invalid, sample_job()],
        source="test-api",
        db_path=db_path,
    )

    assert result["inserted"] == 1
    assert result["failed"] == 1
    assert len(result["errors"]) == 1
    assert count_jobs(db_path) == 1
