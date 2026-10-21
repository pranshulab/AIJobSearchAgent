
import streamlit as st

from app.matcher import CandidateProfile, JobListing, match_job
from app.resume_parser import parse_resume


st.set_page_config(
    page_title="AI Job Search Agent",
    page_icon="🎯",
    layout="wide",
)

st.title("🎯 AI Job Search Agent")
st.caption(
    "Upload your resume, review the extracted profile, "
    "and find jobs that match your skills."
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

if "resume_profile" not in st.session_state:
    st.session_state.resume_profile = None

if "candidate_name" not in st.session_state:
    st.session_state.candidate_name = "Candidate"

if "candidate_email" not in st.session_state:
    st.session_state.candidate_email = ""

if "candidate_phone" not in st.session_state:
    st.session_state.candidate_phone = ""

if "skills_input" not in st.session_state:
    st.session_state.skills_input = "Python, LangChain, RAG"

if "education_text" not in st.session_state:
    st.session_state.education_text = ""

if "projects_text" not in st.session_state:
    st.session_state.projects_text = ""

if "experience_text" not in st.session_state:
    st.session_state.experience_text = ""


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

        # Populate editable fields before rendering the widgets.
        st.session_state.resume_profile = profile
        st.session_state.candidate_name = profile.name or "Candidate"
        st.session_state.candidate_email = profile.email
        st.session_state.candidate_phone = profile.phone
        st.session_state.skills_input = ", ".join(profile.skills)
        st.session_state.education_text = profile.education
        st.session_state.projects_text = profile.projects
        st.session_state.experience_text = profile.experience

        st.success("Resume text extracted. Review every field below.")

    except ValueError as exc:
        st.error(str(exc))


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
        help="Correct the extracted skills. Only keep skills you can demonstrate.",
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
        "The experience duration is entered manually in this version. "
        "It is not inferred from resume dates."
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
    with st.expander("Original extracted text", expanded=False):
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


st.divider()
st.subheader("3. Add a job")

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
            st.error("Enter both a job title and company.")
        elif not required_skills:
            st.error("Enter at least one required skill.")
        elif job_url and not job_url.startswith(
            ("https://", "http://")
        ):
            st.error("The job URL must start with http:// or https://.")
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


st.divider()
st.subheader("4. Ranked job opportunities")

all_jobs = SAMPLE_JOBS + st.session_state.custom_jobs

if not candidate.skills:
    st.warning(
        "No skills are available yet. Upload a resume or enter skills "
        "in the sidebar to start matching."
    )
else:
    results = [
        match_job(candidate, job)
        for job in all_jobs
    ]

    results.sort(
        key=lambda result: result.score,
        reverse=True,
    )

    col1, col2, col3 = st.columns(3)

    col1.metric("Jobs analyzed", len(results))
    col2.metric("Candidate skills", len(set(
        skill.casefold() for skill in candidate.skills
    )))
    col3.metric(
        "Best skill match",
        f"{results[0].score:.1f}%" if results else "N/A",
    )

    st.caption(
        "Skill coverage is not a probability of getting hired."
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

            st.write(
                "**Matched skills:** "
                + (", ".join(result.matched_skills) or "None identified")
            )
            st.write(
                "**Missing skills:** "
                + (", ".join(result.missing_skills) or "None identified")
            )

            if result.job.url:
                st.link_button("Open job listing", result.job.url)

            st.caption(
                "Review the original listing and application materials. "
                "This app does not submit applications."
            )
