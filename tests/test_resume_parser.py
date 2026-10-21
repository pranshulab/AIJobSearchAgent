
import pytest

from app.resume_parser import (
    extract_pdf_text,
    extract_sections,
    extract_skills,
)


def test_extracts_known_skills():
    text = """
    Skills
    Python, LangChain, RAG, Machine Learning, Docker
    """

    skills = extract_skills(text)

    assert "Python" in skills
    assert "LangChain" in skills
    assert "RAG" in skills
    assert "Machine Learning" in skills
    assert "Docker" in skills


def test_skill_matching_is_case_insensitive():
    skills = extract_skills("PYTHON and langchain")

    assert "Python" in skills
    assert "LangChain" in skills


def test_does_not_match_python_inside_word():
    skills = extract_skills("The word micropython appears here.")

    assert "Python" not in skills


def test_extracts_common_resume_sections():
    text = """
    Education
    Master of Computer Applications

    Projects
    Built a document question-answering application.

    Work Experience
    Developed Python applications during an internship.

    Technical Skills
    Python, SQL
    """

    sections = extract_sections(text)

    assert "Master of Computer Applications" in sections["education"]
    assert "document question-answering" in sections["projects"]
    assert "Python applications" in sections["experience"]
    assert "Technical Skills" not in sections["experience"]


def test_empty_pdf_is_rejected():
    with pytest.raises(ValueError, match="empty"):
        extract_pdf_text(b"")


def test_invalid_pdf_is_rejected():
    with pytest.raises(ValueError, match="Unable to read"):
        extract_pdf_text(b"This is not a PDF file.")
