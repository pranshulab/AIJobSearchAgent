
from app.job_store import (
    count_jobs,
    list_jobs,
    normalize_url,
    upsert_job,
)


def sample_job(url="https://example.com/jobs/123"):
    return {
        "external_id": "123",
        "source": "test-api",
        "title": "Junior AI Engineer",
        "company": "Example AI",
        "location": "Remote",
        "description": "Build AI applications.",
        "url": url,
        "skills": ["Python", "RAG"],
        "posted_at": "2026-10-20",
    }


def test_database_starts_empty(tmp_path):
    db_path = tmp_path / "test.db"

    assert count_jobs(db_path) == 0
    assert list_jobs(db_path) == []


def test_insert_and_retrieve_job(tmp_path):
    db_path = tmp_path / "test.db"

    job_id, inserted = upsert_job(
        sample_job(),
        db_path=db_path,
    )

    jobs = list_jobs(db_path)

    assert inserted is True
    assert job_id > 0
    assert len(jobs) == 1
    assert jobs[0]["title"] == "Junior AI Engineer"
    assert jobs[0]["skills"] == ["Python", "RAG"]


def test_duplicate_url_does_not_create_another_job(tmp_path):
    db_path = tmp_path / "test.db"

    first_id, first_inserted = upsert_job(
        sample_job(),
        db_path=db_path,
    )

    second = sample_job(
        "https://example.com/jobs/123?utm_source=email"
    )
    second_id, second_inserted = upsert_job(
        second,
        db_path=db_path,
    )

    assert first_inserted is True
    assert second_inserted is False
    assert first_id == second_id
    assert count_jobs(db_path) == 1


def test_duplicate_refreshes_job_details(tmp_path):
    db_path = tmp_path / "test.db"

    upsert_job(sample_job(), db_path=db_path)

    updated = sample_job()
    updated["description"] = "Updated job description."

    _, inserted = upsert_job(updated, db_path=db_path)

    jobs = list_jobs(db_path)

    assert inserted is False
    assert len(jobs) == 1
    assert jobs[0]["description"] == "Updated job description."


def test_url_normalization_removes_tracking_parameters():
    assert normalize_url(
        "https://Example.com/jobs/123?utm_source=email#details"
    ) == "https://example.com/jobs/123"
