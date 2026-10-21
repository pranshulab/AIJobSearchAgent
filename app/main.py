
import streamlit as st

from app.matcher import CandidateProfile, JobListing, match_job


st.set_page_config(
    page_title="AI Job Search Agent",
    page_icon="🎯",
    layout="wide",
)

st.title("🎯 AI Job Search Agent")
st.caption(
    "Discover relevant jobs, evaluate skill matches, "
    "and prepare for human-reviewed applications."
)

SAMPLE_JOBS = [
    JobListing(
        title="Junior GenAI Engineer",
        company="Example AI Labs",
        location="Remote",
        required_skills=["Python", "LangChain", "RAG", "Docker"],
        url="https://www.linkedin.com/jobs/",
    ),
    JobListing(
        title="Machine Learning Engineer",
        company="Example Data Systems",
        location="India",
        required_skills=["Python", "Machine Learning", "SQL"],
        url="https://www.linkedin.com/jobs/",
    ),
    JobListing(
        title="Python Backend Developer",
        company="Example Software",
        location="Hybrid",
        required_skills=["Python", "FastAPI", "SQL", "Docker"],
        url="https://www.linkedin.com/jobs/",
    ),
]

if "custom_jobs" not in st.session_state:
    st.session_state.custom_jobs = []


with st.sidebar:
    st.header("Candidate profile")

    candidate_name = st.text_input(
        "Name",
        value="Candidate",
    )

    skills_input = st.text_area(
        "Your skills (comma-separated)",
        value="Python, LangChain, RAG",
        help="Enter skills you can honestly demonstrate.",
    )

    experience_years = st.number_input(
        "Years of experience",
        min_value=0.0,
        max_value=60.0,
        value=0.0,
        step=0.5,
    )

    st.info(
        "Phase 1 uses explicit skill matching. "
        "Resume parsing and local LLM inference come later."
    )


candidate = CandidateProfile(
    name=candidate_name.strip() or "Candidate",
    skills=[
        skill.strip()
        for skill in skills_input.split(",")
        if skill.strip()
    ],
    experience_years=experience_years,
)

st.subheader("Add a job")

with st.form("add_job_form", clear_on_submit=True):
    job_title = st.text_input("Job title")
    company = st.text_input("Company")
    location = st.text_input("Location", value="India")
    required_skills_input = st.text_input(
        "Required skills (comma-separated)"
    )
    job_url = st.text_input("Job URL (optional)")

    submitted = st.form_submit_button("Add job")

    if submitted:
        required_skills = [
            skill.strip()
            for skill in required_skills_input.split(",")
            if skill.strip()
        ]

        if not job_title.strip() or not company.strip():
            st.error("Please enter both a job title and company.")
        elif not required_skills:
            st.error("Enter at least one required skill.")
        elif job_url and not job_url.startswith(("https://", "http://")):
            st.error("The job URL must begin with http:// or https://.")
        else:
            st.session_state.custom_jobs.append(
                JobListing(
                    title=job_title.strip(),
                    company=company.strip(),
                    location=location.strip(),
                    required_skills=required_skills,
                    url=job_url.strip(),
                )
            )
            st.success("Job added to this session.")


all_jobs = SAMPLE_JOBS + st.session_state.custom_jobs

st.divider()
st.subheader("Ranked job opportunities")

if not candidate.skills:
    st.warning("Enter at least one candidate skill in the sidebar.")
else:
    results = [
        match_job(candidate, job)
        for job in all_jobs
    ]

    results.sort(key=lambda result: result.score, reverse=True)

    col1, col2, col3 = st.columns(3)

    col1.metric("Jobs analyzed", len(results))
    col2.metric("Candidate skills", len({
        skill.strip().casefold()
        for skill in candidate.skills
        if skill.strip()
    }))
    col3.metric(
        "Best skill match",
        f"{results[0].score:.1f}%" if results else "N/A",
    )

    st.caption(
        "Scores measure required-skill coverage only. "
        "They do not predict interview or hiring probability."
    )

    for result in results:
        with st.container(border=True):
            st.subheader(result.job.title)
            st.write(
                f"**Company:** {result.job.company}  \n"
                f"**Location:** {result.job.location}"
            )

            st.progress(
                int(result.score),
                text=f"Skill coverage: {result.score:.1f}%",
            )

            matched_text = (
                ", ".join(result.matched_skills)
                or "None identified"
            )
            missing_text = (
                ", ".join(result.missing_skills)
                or "None identified"
            )

            st.write(f"**Matched skills:** {matched_text}")
            st.write(f"**Missing skills:** {missing_text}")

            if result.job.url:
                st.link_button(
                    "Open job listing",
                    result.job.url,
                )

            st.caption(
                "Review the original listing and your qualifications "
                "before applying. No application is submitted by this app."
            )
