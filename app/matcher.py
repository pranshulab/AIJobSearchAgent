
from dataclasses import dataclass


@dataclass
class CandidateProfile:
    name: str
    skills: list[str]
    experience_years: float = 0.0


@dataclass
class JobListing:
    title: str
    company: str
    location: str
    required_skills: list[str]
    url: str = ""
    description: str=""


@dataclass
class MatchResult:
    job: JobListing
    score: float
    matched_skills: list[str]
    missing_skills: list[str]


def normalize_skill(skill: str) -> str:
    """Normalize a skill for case-insensitive comparison."""
    return " ".join(skill.strip().casefold().split())


def match_job(
    candidate: CandidateProfile,
    job: JobListing,
) -> MatchResult:
    """Compare candidate skills with a job's required skills.

    The score is the percentage of unique required skills
    explicitly matched by the candidate.
    """
    candidate_skills = {
        normalize_skill(skill)
        for skill in candidate.skills
        if normalize_skill(skill)
    }

    required_skills = {
        normalize_skill(skill)
        for skill in job.required_skills
        if normalize_skill(skill)
    }

    matched = candidate_skills & required_skills
    missing = required_skills - candidate_skills

    score = (
        round(len(matched) / len(required_skills) * 100, 2)
        if required_skills
        else 0.0
    )

    # Preserve readable skill names from the job listing.
    matched_names = sorted(
        {
            skill.strip()
            for skill in job.required_skills
            if normalize_skill(skill) in matched
        },
        key=str.casefold,
    )

    missing_names = sorted(
        {
            skill.strip()
            for skill in job.required_skills
            if normalize_skill(skill) in missing
        },
        key=str.casefold,
    )

    return MatchResult(
        job=job,
        score=score,
        matched_skills=matched_names,
        missing_skills=missing_names,
    )
