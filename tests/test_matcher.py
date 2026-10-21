
from app.matcher import CandidateProfile, JobListing, match_job


def test_all_required_skills_match():
    candidate = CandidateProfile(
        name="Test Candidate",
        skills=["Python", "RAG"],
    )
    job = JobListing(
        title="AI Engineer",
        company="Example",
        location="Remote",
        required_skills=["Python", "RAG"],
    )

    result = match_job(candidate, job)

    assert result.score == 100.0
    assert set(result.matched_skills) == {"Python", "RAG"}
    assert result.missing_skills == []


def test_partial_skill_match():
    candidate = CandidateProfile(
        name="Test Candidate",
        skills=["Python", "RAG"],
    )
    job = JobListing(
        title="AI Engineer",
        company="Example",
        location="Remote",
        required_skills=["Python", "RAG", "Docker", "SQL"],
    )

    result = match_job(candidate, job)

    assert result.score == 50.0
    assert set(result.matched_skills) == {"Python", "RAG"}
    assert set(result.missing_skills) == {"Docker", "SQL"}


def test_matching_is_case_insensitive():
    candidate = CandidateProfile(
        name="Test Candidate",
        skills=[" python ", "LANGCHAIN"],
    )
    job = JobListing(
        title="AI Engineer",
        company="Example",
        location="Remote",
        required_skills=["Python", "LangChain"],
    )

    result = match_job(candidate, job)

    assert result.score == 100.0


def test_empty_required_skills_gives_zero():
    candidate = CandidateProfile(
        name="Test Candidate",
        skills=["Python"],
    )
    job = JobListing(
        title="Developer",
        company="Example",
        location="Remote",
        required_skills=[],
    )

    result = match_job(candidate, job)

    assert result.score == 0.0
    assert result.matched_skills == []
    assert result.missing_skills == []


def test_duplicate_required_skills_do_not_inflate_score():
    candidate = CandidateProfile(
        name="Test Candidate",
        skills=["Python"],
    )
    job = JobListing(
        title="Developer",
        company="Example",
        location="Remote",
        required_skills=["Python", "python", "SQL"],
    )

    result = match_job(candidate, job)

    assert result.score == 50.0
    assert set(result.matched_skills) == {"Python", "python"}
    assert set(result.missing_skills) == {"SQL"}
