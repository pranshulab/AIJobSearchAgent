
from app.matcher import CandidateProfile, JobListing
from app.semantic_matcher import analyze_job


def make_candidate():
    return CandidateProfile(
        name="Test Candidate",
        skills=["Python", "RAG", "LangChain"],
    )


def make_job():
    return JobListing(
        title="Junior GenAI Engineer",
        company="Example AI",
        location="Remote",
        required_skills=["RAG", "Python", "Docker"],
        description=(
            "Build retrieval-augmented generation applications "
            "and deploy services using Docker."
        ),
    )


def test_semantic_matching_uses_evidence():
    candidate = make_candidate()
    job = make_job()

    def fake_llm(system_prompt, user_prompt):
        return {
            "summary": "Build RAG applications and deploy services.",
            "requirements": [
                {
                    "requirement": "RAG",
                    "status": "matched",
                    "evidence": "RAG",
                    "reason": "The candidate lists RAG.",
                },
                {
                    "requirement": "Python",
                    "status": "matched",
                    "evidence": "Python",
                    "reason": "The candidate lists Python.",
                },
                {
                    "requirement": "Docker",
                    "status": "missing",
                    "evidence": "",
                    "reason": "No Docker evidence was supplied.",
                },
                {
                    "requirement": (
                        "Build retrieval-augmented generation applications"
                    ),
                    "status": "matched",
                    "evidence": "RAG",
                    "reason": "RAG is relevant to this requirement.",
                },
            ],
        }

    result = analyze_job(
        candidate,
        job,
        resume_text="Skills: Python, RAG, LangChain",
        llm_function=fake_llm,
    )

    assert result.method == "local_llm"
    assert result.score > 0
    assert result.summary
    assert "Docker" in result.missing_requirements


def test_unsupported_evidence_is_rejected():
    candidate = make_candidate()
    job = make_job()

    def fake_llm(system_prompt, user_prompt):
        return {
            "summary": "Build AI applications.",
            "requirements": [
                {
                    "requirement": "Docker",
                    "status": "matched",
                    "evidence": "I have five years of Docker experience",
                    "reason": "Claimed experience.",
                }
            ],
        }

    result = analyze_job(
        candidate,
        job,
        resume_text="Skills: Python, RAG, LangChain",
        llm_function=fake_llm,
    )

    docker_result = next(
        item for item in result.requirements
        if item["requirement"] == "Docker"
    )

    assert docker_result["status"] == "missing"
    assert docker_result["evidence"] == ""


def test_fallback_works_without_llm():
    candidate = make_candidate()
    job = make_job()

    result = analyze_job(
        candidate,
        job,
        use_llm=False,
    )

    assert result.method == "keyword_fallback"
    assert abs(result.score - (200 / 3)) < 0.01
    assert "Python" in result.matched_requirements
    assert "Docker" in result.missing_requirements


def test_invalid_llm_response_uses_fallback():
    candidate = make_candidate()
    job = make_job()

    def broken_llm(system_prompt, user_prompt):
        raise RuntimeError("Simulated model failure")

    result = analyze_job(
        candidate,
        job,
        llm_function=broken_llm,
    )

    assert result.method == "keyword_fallback"
    assert result.fallback_reason
