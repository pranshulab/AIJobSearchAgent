
import re
from dataclasses import dataclass
from io import BytesIO

from pypdf import PdfReader


@dataclass
class ResumeProfile:
    name: str = ""
    email: str = ""
    phone: str = ""
    skills: list[str] | None = None
    education: str = ""
    projects: str = ""
    experience: str = ""
    raw_text: str = ""

    def __post_init__(self):
        if self.skills is None:
            self.skills = []


# This dictionary is deliberately explicit and editable.
# Add or remove skills as the project evolves.
SKILL_KEYWORDS = {
    "Python": ["python"],
    "Java": ["java"],
    "SQL": ["sql", "structured query language"],
    "Machine Learning": ["machine learning", "machine-learning"],
    "Deep Learning": ["deep learning"],
    "NLP": ["natural language processing", "nlp"],
    "LLMs": ["large language models", "llm", "llms"],
    "LangChain": ["langchain"],
    "LangGraph": ["langgraph"],
    "RAG": ["retrieval augmented generation", "rag"],
    "FastAPI": ["fastapi"],
    "Flask": ["flask"],
    "Django": ["django"],
    "Streamlit": ["streamlit"],
    "Pandas": ["pandas"],
    "NumPy": ["numpy"],
    "Matplotlib": ["matplotlib"],
    "Seaborn": ["seaborn"],
    "Scikit-learn": ["scikit-learn", "sklearn"],
    "TensorFlow": ["tensorflow"],
    "PyTorch": ["pytorch"],
    "Hugging Face": ["hugging face", "huggingface"],
    "FAISS": ["faiss"],
    "ChromaDB": ["chromadb", "chroma db"],
    "Docker": ["docker"],
    "Git": ["git", "github"],
    "REST APIs": ["rest api", "rest apis", "restful api"],
    "SQLAlchemy": ["sqlalchemy"],
    "PostgreSQL": ["postgresql", "postgres"],
    "MySQL": ["mysql"],
    "MongoDB": ["mongodb", "mongo db"],
    "HTML": ["html"],
    "CSS": ["css"],
    "JavaScript": ["javascript"],
}


SECTION_ALIASES = {
    "education": {
        "education",
        "academic background",
        "academic qualifications",
        "qualifications",
    },
    "projects": {
        "projects",
        "personal projects",
        "academic projects",
        "project experience",
    },
    "experience": {
        "experience",
        "work experience",
        "professional experience",
        "employment history",
        "internship experience",
        "internships",
    },
}


def extract_pdf_text(
    pdf_bytes: bytes,
    max_size_mb: int = 10,
    max_pages: int = 30,
) -> str:
    """Extract text from a PDF provided as bytes."""

    if not pdf_bytes:
        raise ValueError("The uploaded PDF is empty.")

    if len(pdf_bytes) > max_size_mb * 1024 * 1024:
        raise ValueError(
            f"PDF exceeds the {max_size_mb} MB size limit."
        )

    try:
        reader = PdfReader(BytesIO(pdf_bytes), strict=True)

        if reader.is_encrypted:
            raise ValueError(
                "This PDF is encrypted. Upload an accessible PDF."
            )

        if len(reader.pages) > max_pages:
            raise ValueError(
                f"PDF exceeds the {max_pages}-page limit."
            )

        pages = [
            page.extract_text() or ""
            for page in reader.pages
        ]

    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(
            "Unable to read this PDF. Check that it is a valid PDF."
        ) from exc

    text = "\n".join(pages).strip()

    if not text:
        raise ValueError(
            "No selectable text was found. "
            "This may be a scanned PDF requiring OCR."
        )

    return text


def extract_skills(text: str) -> list[str]:
    """Find explicitly listed skills using case-insensitive matching."""

    normalized_text = text.casefold()
    found = []

    for display_name, aliases in SKILL_KEYWORDS.items():
        for alias in aliases:
            pattern = (
                r"(?<!\w)"
                + re.escape(alias.casefold())
                + r"(?!\w)"
            )

            if re.search(pattern, normalized_text):
                found.append(display_name)
                break

    return found


def _normalize_heading(line: str) -> str:
    """Normalize a probable section heading."""

    return re.sub(
        r"[^a-z ]",
        "",
        line.casefold().strip(),
    ).strip()


def extract_sections(text: str) -> dict[str, str]:
    """Extract text under common resume section headings."""

    aliases = {
        alias: section
        for section, names in SECTION_ALIASES.items()
        for alias in names
    }

    sections = {
        "education": [],
        "projects": [],
        "experience": [],
    }

    current_section = None

    for line in text.splitlines():
        heading = _normalize_heading(line)

        if heading in aliases:
            current_section = aliases[heading]
            continue

        # A recognized, unrelated heading ends the current section.
        if heading in {
            "skills",
            "technical skills",
            "certifications",
            "certificates",
            "summary",
            "professional summary",
            "objective",
            "contact",
            "contact information",
            "achievements",
            "languages",
            "interests",
            "hobbies",
            "references",
        }:
            current_section = None
            continue

        if current_section and line.strip():
            sections[current_section].append(line.strip())

    return {
        section: "\n".join(lines).strip()
        for section, lines in sections.items()
    }


def parse_resume(pdf_bytes: bytes) -> ResumeProfile:
    """Convert an uploaded PDF into a reviewable profile."""

    text = extract_pdf_text(pdf_bytes)
    sections = extract_sections(text)

    email_match = re.search(
        r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
        text,
        re.IGNORECASE,
    )

    phone_match = re.search(
        r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)",
        text,
    )

    # Name extraction is intentionally conservative:
    # review it in the UI instead of trusting a guess.
    first_lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    name = first_lines[0][:100] if first_lines else ""

    return ResumeProfile(
        name=name,
        email=email_match.group(0) if email_match else "",
        phone=phone_match.group(0).strip() if phone_match else "",
        skills=extract_skills(text),
        education=sections["education"],
        projects=sections["projects"],
        experience=sections["experience"],
        raw_text=text,
    )
