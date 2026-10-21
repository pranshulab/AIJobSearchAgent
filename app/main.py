
import streamlit as st

from app.matcher import CandidateProfile, JobListing
from app.resume_parser import parse_resume
from app.job_api import fetch_authorized_jobs
from app.job_ingestion import ingest_jobs
from app.job_store import init_db, list_jobs
from app.semantic_matcher import analyze_job

# --------------------------------------------------
# 1. Application configuration and database
# --------------------------------------------------

st.set_page_config(
    page_title="AI Job Search Agent",
    page_icon="🎯",
    layout="wide",
)

# Initialize SQLite database and create tables if needed.
init_db()


# --------------------------------------------------
# 2. Application header
# --------------------------------------------------

st.title("🎯 AI Job Search Agent")
st.caption(
    "Upload your resume, discover relevant jobs, "
    "and prepare applications with human-controlled submission."
)


# --------------------------------------------------
# 3. Sample jobs for development and testing
# --------------------------------------------------

SAMPLE_JOBS = [
    JobListing(
        title="Junior GenAI Engineer",
        company="Example AI Labs",
        location="Remote",
        required_skills=["Python", "LangChain", "RAG", "Docker"],
        url="https://www.linkedin.com/jobs/",
        description=(
            "Build retrieval-augmented generation (RAG) applications, "
            "integrate LangChain and vector databases, write Python services, "
            "and package applications with Docker."
        ),
    ),
    JobListing(
        title="Machine Learning Engineer",
        company="Example Data Systems",
        location="India",
        required_skills=["Python", "Machine Learning", "SQL"],
        url="https://www.linkedin.com/jobs/",
        description=(
            "Develop and evaluate machine learning models using Python, "
            "prepare datasets, analyze model performance, and query data with SQL."
        ),
    ),
    JobListing(
        title="Python Backend Developer",
        company="Example Software",
        location="Hybrid",
        required_skills=["Python", "FastAPI", "SQL", "Docker"],
        url="https://www.linkedin.com/jobs/",
        description=(
            "Develop Python backend APIs with FastAPI, work with SQL databases, "
            "and package services for deployment using Docker."
        ),
    ),
]


# --------------------------------------------------
# 4. Initialize Streamlit session state
# --------------------------------------------------

DEFAULTS = {
    "resume_profile": None,
    "candidate_name": "Candidate",
    "candidate_email": "",
    "candidate_phone": "",
    "skills_input": "Python, LangChain, RAG",
    "education_text": "",
    "projects_text": "",
    "experience_text": "",
    "custom_jobs": [],
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# --------------------------------------------------
# 5. Resume upload and parsing
# --------------------------------------------------

st.subheader("1. Upload your resume")

uploaded_file = st.file_uploader(
    "Choose a text-based PDF resume",
    type=["pdf"],
    help="Maximum 10 MB and 30 pages. Scanned PDFs require OCR.",
)

if st.button(
    "Extract resume information",
    disabled=uploaded_file is None,
):
    try:
        profile = parse_resume(uploaded_file.getvalue())

        st.session_state.resume_profile = profile
        st.session_state.candidate_name = profile.name or "Candidate"
        st.session_state.candidate_email = profile.email
        st.session_state.candidate_phone = profile.phone
        st.session_state.skills_input = ", ".join(profile.skills)
        st.session_state.education_text = profile.education
        st.session_state.projects_text = profile.projects
        st.session_state.experience_text = profile.experience

        st.success(
            "Resume extracted successfully. "
            "Review the detected information before using it."
        )

    except ValueError as exc:
        st.error(str(exc))


# --------------------------------------------------
# 6. Candidate profile
# --------------------------------------------------

st.divider()
st.subheader("2. Review your candidate profile")

with st.sidebar:
    st.header("Candidate profile")

    candidate_name = st.text_input(
        "Name",
        key="candidate_name",
    )

    candidate_email = st.text_input(
        "Email",
        key="candidate_email",
    )

    candidate_phone = st.text_input(
        "Phone",
        key="candidate_phone",
    )

    skills_input = st.text_area(
        "Skills (comma-separated)",
        key="skills_input",
        help="Keep only skills you can honestly demonstrate.",
    )

    experience_years = st.number_input(
        "Years of experience",
        min_value=0.0,
        max_value=60.0,
        value=0.0,
        step=0.5,
        key="experience_years",
    )

    st.caption(
        "Experience duration is entered manually. "
        "It is not inferred from resume dates."
    )

    use_local_llm = st.checkbox(
        "Use local LLM for semantic matching",
        value=True,
        help=(
            "Runs the configured GGUF model directly in Python. "
            "If it fails, the app falls back to keyword matching."
        ),
    )


with st.expander("Education", expanded=False):
    st.text_area(
        "Extracted education",
        key="education_text",
        height=120,
    )

with st.expander("Projects", expanded=False):
    st.text_area(
        "Extracted projects",
        key="projects_text",
        height=160,
    )

with st.expander("Experience", expanded=False):
    st.text_area(
        "Extracted experience",
        key="experience_text",
        height=160,
    )

if st.session_state.resume_profile is not None:
    with st.expander("Original extracted resume text"):
        st.text(st.session_state.resume_profile.raw_text)


candidate = CandidateProfile(
    name=candidate_name.strip() or "Candidate",
    skills=[
        skill.strip()
        for skill in skills_input.split(",")
        if skill.strip()
    ],
    experience_years=experience_years,
)


# --------------------------------------------------
# 7. Add jobs manually and save to SQLite
# --------------------------------------------------

st.divider()
st.subheader("3. Add a job manually")

with st.form("add_job_form", clear_on_submit=True):
    job_title = st.text_input("Job title")
    company = st.text_input("Company")
    location = st.text_input("Location", value="India")

    required_skills_input = st.text_input(
        "Required skills (comma-separated)"
    )

    job_description = st.text_area(
        "Full job description",
        height=180,
        help="Paste the job description so the local model can analyze its meaning.",
    )

    job_url = st.text_input("Job URL (optional)")

    submitted = st.form_submit_button("Save job to database")

    if submitted:
        required_skills = [
            skill.strip()
            for skill in required_skills_input.split(",")
            if skill.strip()
        ]

        if not job_title.strip() or not company.strip():
            st.error("Please enter both the job title and company.")

        elif not required_skills:
            st.error("Please enter at least one required skill.")

        elif job_url and not job_url.startswith(
            ("https://", "http://")
        ):
            st.error(
                "The job URL must start with https:// or http://."
            )

        else:
            record = {
                "title": job_title,
                "company": company,
                "location": location,
                "description": job_description.strip(),
                "url": job_url.strip(),
                "skills": required_skills,
            }

            try:
                report = ingest_jobs(
                    [record],
                    source="manual",
                )

                if report["inserted"]:
                    st.success("New job saved to SQLite.")

                elif report["updated"]:
                    st.success(
                        "This job already exists. "
                        "Its details have been updated."
                    )

                else:
                    errors = report.get("errors", [])
                    st.error(
                        "Could not save the job: "
                        + str(errors)
                    )

            except (ValueError, RuntimeError) as exc:
                st.error(f"Unable to save job: {exc}")


# --------------------------------------------------
# 8. Fetch jobs from an authorized API
# --------------------------------------------------

st.divider()
st.subheader("4. Import jobs from an authorized API")

st.caption(
    "Configure JOB_API_URL in your environment to use an "
    "authorized HTTPS JSON API compatible with app/job_api.py."
)

if st.button("Fetch and save API jobs"):
    try:
        records = fetch_authorized_jobs()

        report = ingest_jobs(
            records,
            source="authorized-api",
        )

        st.success(
            f"Received {report['received']} jobs: "
            f"{report['inserted']} new, "
            f"{report['updated']} updated, "
            f"{report['failed']} failed."
        )

        for error in report["errors"][:10]:
            st.warning(
                f"Record {error['index']}: {error['error']}"
            )

    except RuntimeError as exc:
        st.error(str(exc))


# --------------------------------------------------
# 9. Load persisted jobs from SQLite
# --------------------------------------------------

st.divider()
st.subheader("5. Ranked job opportunities")

try:
    stored_jobs = list_jobs()

except Exception as exc:
    st.error(f"Unable to load saved jobs: {exc}")
    stored_jobs = []


database_jobs = [
    JobListing(
        title=job["title"],
        company=job["company"],
        location=job["location"],
        required_skills=job["skills"],
        url=job["url"],
        description=job.get("description", ""),
    )
    for job in stored_jobs
]


# Sample jobs are for demonstration only.
# Persisted jobs remain available across application restarts.
all_jobs = SAMPLE_JOBS + database_jobs


# --------------------------------------------------
# 10. Semantic analysis and ranked job opportunities
# --------------------------------------------------

if "semantic_results" not in st.session_state:
    st.session_state.semantic_results = []

resume_profile = st.session_state.resume_profile
resume_text = resume_profile.raw_text if resume_profile is not None else ""

st.caption(
    "Semantic analysis compares job requirements against your listed skills "
    "and supplied resume evidence. Click Analyze again after changing your "
    "candidate profile or job descriptions."
)

if st.button("Analyze and rank jobs"):
    if not candidate.skills and not resume_text.strip():
        st.warning(
            "Enter candidate skills or upload a resume before matching."
        )
        st.session_state.semantic_results = []
    elif not all_jobs:
        st.warning("No jobs are available to analyze yet.")
        st.session_state.semantic_results = []
    else:
        analyzed = []
        progress = st.progress(0, text="Analyzing jobs...")

        for index, job in enumerate(all_jobs):
            result = analyze_job(
                candidate=candidate,
                job=job,
                resume_text=resume_text,
                use_llm=use_local_llm,
            )
            analyzed.append((job, result))
            progress.progress(
                int((index + 1) / len(all_jobs) * 100),
                text=f"Analyzed {index + 1} of {len(all_jobs)} jobs",
            )

        st.session_state.semantic_results = sorted(
            analyzed,
            key=lambda item: item[1].score,
            reverse=True,
        )
        progress.empty()
        st.success("Job analysis completed.")

results = st.session_state.semantic_results

if results:
    col1, col2, col3 = st.columns(3)

    col1.metric("Jobs analyzed", len(results))
    col2.metric(
        "Candidate skills",
        len({
            skill.strip().casefold()
            for skill in candidate.skills
            if skill.strip()
        }),
    )
    col3.metric("Best match score", f"{results[0][1].score:.1f}%")

    for job, result in results:
        with st.container(border=True):
            st.subheader(job.title)
            st.write(f"**Company:** {job.company}  \n**Location:** {job.location}")

            st.progress(
                max(0, min(100, int(result.score))),
                text=f"Requirement coverage: {result.score:.1f}%",
            )

            st.markdown("**Job summary**")
            st.write(result.summary)

            method_label = (
                "Local LLM (GGUF)"
                if result.method == "local_llm"
                else "Keyword fallback"
            )
            st.caption(f"Analysis method: {method_label}")

            if result.fallback_reason:
                with st.expander("Why keyword fallback was used"):
                    st.write(result.fallback_reason)

            st.markdown("**Requirement analysis**")
            if result.matched_requirements:
                st.write(
                    "✅ **Matched:** "
                    + ", ".join(result.matched_requirements)
                )
            if result.partial_requirements:
                st.write(
                    "🟡 **Partial:** "
                    + ", ".join(result.partial_requirements)
                )
            if result.missing_requirements:
                st.write(
                    "❌ **Missing:** "
                    + ", ".join(result.missing_requirements)
                )

            with st.expander("Inspect requirement evidence"):
                for item in result.requirements:
                    st.markdown(
                        f"**{item['requirement']} — {item['status']}**"
                    )
                    if item["evidence"]:
                        st.write(f"Resume evidence: {item['evidence']}")
                    if item["reason"]:
                        st.caption(item["reason"])

            if job.url:
                st.link_button("Open job listing", job.url)

            st.caption(
                "This score is a decision-support estimate of requirement "
                "coverage, not a probability of being hired. Verify the "
                "original listing and evidence. You remain responsible for "
                "final application submission."
            )
else:
    st.info("Click **Analyze and rank jobs** to compare your profile with available jobs.")


# --------------------------------------------------
# 11. Database summary
# --------------------------------------------------

st.divider()
st.subheader("6. Database summary")

st.metric(
    "Persisted job listings",
    len(stored_jobs),
)

st.caption(
    "Saved jobs are stored locally in data/jobs.db. "
    "Sample jobs are not included in this database count."
)
