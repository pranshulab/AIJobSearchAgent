
# AI Job Search Agent

A human-controlled job discovery and matching assistant built
with Python and Streamlit.

## Current features

- Candidate skill profile
- Sample job listings
- Manual job entry
- Skill coverage scoring
- Matched and missing skill reports
- Job listing links
- Automated tests

## Requirements

- Python 3.11 or 3.12
- Git

## Setup on Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Run the application

```powershell
python -m streamlit run app/main.py
```

## Run tests

```powershell
python -m pytest -v
```

## Scope

This version uses deterministic Python skill matching.
Live job ingestion, local LLM inference, resume generation,
persistent storage, and Docker deployment are planned for
later phases.

The user reviews job listings and controls all final submissions.
