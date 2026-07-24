"""
RAG-ALL: Editor Service - Main Application
Professional formatting + Quality checks cho research outputs.

Editor Features:
  - Academic formatting (APA, MLA, Chicago, IEEE)
  - Grammar & style checking
  - Readability analysis
  - Structure validation
  - Export to multiple formats (Markdown, PDF, DOCX)
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any

from shared.config.settings import settings
from shared.utils.logger import editor_logger as logger


# =============================================================================
# Lifespan
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting Editor Service...")
    yield
    logger.info("🔄 Shutting down Editor Service...")


# =============================================================================
# FastAPI App
# =============================================================================

app = FastAPI(
    title="RAG-ALL Editor Service",
    description="Professional academic editing & formatting",
    version="0.1.0",
    lifespan=lifespan,
)


# =============================================================================
# Request/Response Models
# =============================================================================

class EditRequest(BaseModel):
    text: str
    format: str = "markdown"  # markdown, apa, mla, chicago, ieee
    language: str = "vi"  # vi, en
    check_grammar: bool = True
    check_readability: bool = True
    check_structure: bool = True


class EditResponse(BaseModel):
    original_text: str
    edited_text: str
    grammar_issues: list[dict] = []
    readability_score: float = 0.0
    readability_level: str = ""
    structure_issues: list[dict] = []
    suggestions: list[str] = []
    word_count: int = 0
    char_count: int = 0


class FormatRequest(BaseModel):
    text: str
    target_format: str = "markdown"  # markdown, html, docx, pdf
    citation_style: str = "apa"  # apa, mla, chicago, ieee


class FormatResponse(BaseModel):
    formatted_text: str
    format: str
    metadata: dict = {}


# =============================================================================
# Grammar Checker
# =============================================================================

class GrammarChecker:
    """Grammar and style checking."""

    def __init__(self):
        pass

    def check(self, text: str, language: str = "vi") -> list[dict]:
        """
        Check grammar and style.

        Returns:
            List of issues with position and suggestion
        """
        issues = []

        # Basic checks (can be enhanced with language_tool_python)
        import re

        # Check for common issues
        patterns = [
            # Double spaces
            (r'  +', "Multiple spaces", "Reduce to single space"),
            # Trailing spaces
            (r' +\n', "Trailing spaces", "Remove trailing spaces"),
            # Missing period at end of sentences
            (r'[^.!?]\s*$', "Missing punctuation", "Add period at end"),
        ]

        for pattern, issue_type, suggestion in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                issues.append({
                    "type": "style",
                    "position": match.start(),
                    "length": len(match.group()),
                    "issue": issue_type,
                    "suggestion": suggestion,
                })

        # Try language_tool_python if available
        try:
            import language_tool_python
            tool = language_tool_python.LanguageTool(language)
            matches = tool.check(text)
            for match in matches[:20]:  # Limit to 20 issues
                issues.append({
                    "type": "grammar",
                    "position": match.offset,
                    "length": match.errorLength,
                    "issue": match.message,
                    "suggestion": match.replacements[0] if match.replacements else "",
                })
        except ImportError:
            logger.info("language_tool_python not available, using basic checks")

        return issues


# =============================================================================
# Readability Analyzer
# =============================================================================

class ReadabilityAnalyzer:
    """Analyze text readability."""

    def analyze(self, text: str) -> dict:
        """
        Calculate readability metrics.

        Returns:
            {score, level, suggestions}
        """
        import re

        # Split into sentences and words
        sentences = re.split(r'[.!?]+', text)
        words = text.split()

        num_sentences = len([s for s in sentences if s.strip()])
        num_words = len(words)
        num_chars = len(text.replace(" ", ""))

        # Flesch Reading Ease (Vietnamese adaptation)
        if num_sentences > 0 and num_words > 0:
            avg_sentence_length = num_words / num_sentences
            avg_word_length = num_chars / num_words

            # Simplified Flesch for Vietnamese
            score = 206.835 - 1.015 * avg_sentence_length - 84.6 * (avg_word_length / 5)
            score = max(0, min(100, score))
        else:
            score = 0

        # Determine level
        if score >= 80:
            level = "Very Easy"
        elif score >= 60:
            level = "Easy"
        elif score >= 40:
            level = "Moderate"
        elif score >= 20:
            level = "Difficult"
        else:
            level = "Very Difficult"

        return {
            "score": round(score, 2),
            "level": level,
            "avg_sentence_length": round(avg_sentence_length, 1) if num_sentences > 0 else 0,
            "avg_word_length": round(avg_word_length, 1) if num_words > 0 else 0,
        }


# =============================================================================
# Structure Validator
# =============================================================================

class StructureValidator:
    """Validate document structure."""

    def validate(self, text: str) -> list[dict]:
        """
        Check document structure.

        Returns:
            List of structure issues
        """
        issues = []
        lines = text.split("\n")

        # Check for headers
        headers = [l for l in lines if l.strip().startswith("#")]
        if not headers:
            issues.append({
                "type": "structure",
                "issue": "No headers found",
                "suggestion": "Add headers to organize content",
            })

        # Check for paragraphs
        paragraphs = [l for l in lines if l.strip() and not l.startswith("#")]
        if len(paragraphs) < 3:
            issues.append({
                "type": "structure",
                "issue": "Very few paragraphs",
                "suggestion": "Break content into more paragraphs",
            })

        # Check for empty lines between sections
        for i, line in enumerate(lines):
            if line.startswith("#") and i > 0 and lines[i-1].strip() != "":
                issues.append({
                    "type": "structure",
                    "position": i,
                    "issue": "Missing blank line before header",
                    "suggestion": "Add empty line before header",
                })

        return issues


# =============================================================================
# Format Converter
# =============================================================================

class FormatConverter:
    """Convert between document formats."""

    def convert(self, text: str, target_format: str, citation_style: str = "apa") -> dict:
        """Convert text to target format."""
        if target_format == "markdown":
            return {"formatted_text": text, "format": "markdown"}
        elif target_format == "html":
            return {"formatted_text": self._to_html(text), "format": "html"}
        elif target_format == "docx":
            return self._to_docx(text)
        elif target_format == "pdf":
            return self._to_pdf(text)
        else:
            return {"formatted_text": text, "format": "markdown"}

    def _to_html(self, text: str) -> str:
        """Convert markdown to HTML."""
        import re

        # Simple markdown to HTML conversion
        html = text
        html = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
        html = re.sub(r'\n\n', '</p><p>', html)
        html = f'<p>{html}</p>'

        return html

    def _to_docx(self, text: str) -> dict:
        """Convert to DOCX format."""
        # Placeholder - would use python-docx
        return {
            "formatted_text": text,
            "format": "docx",
            "metadata": {"note": "DOCX export requires python-docx"},
        }

    def _to_pdf(self, text: str) -> dict:
        """Convert to PDF format."""
        # Placeholder - would use reportlab or weasyprint
        return {
            "formatted_text": text,
            "format": "pdf",
            "metadata": {"note": "PDF export requires reportlab/weasyprint"},
        }


# =============================================================================
# Initialize & Endpoints
# =============================================================================

grammar_checker = GrammarChecker()
readability_analyzer = ReadabilityAnalyzer()
structure_validator = StructureValidator()
format_converter = FormatConverter()


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "editor"}


@app.post("/edit", response_model=EditResponse)
async def edit_text(request: EditRequest) -> EditResponse:
    """Edit and improve text quality."""
    logger.info(f"Edit request: {len(request.text)} chars, format={request.format}")

    grammar_issues = []
    readability = {"score": 0, "level": ""}
    structure_issues = []

    if request.check_grammar:
        grammar_issues = grammar_checker.check(request.text, request.language)

    if request.check_readability:
        readability = readability_analyzer.analyze(request.text)

    if request.check_structure:
        structure_issues = structure_validator.validate(request.text)

    # Generate suggestions
    suggestions = []
    if grammar_issues:
        suggestions.append(f"Found {len(grammar_issues)} grammar/style issues")
    if readability.get("score", 0) < 50:
        suggestions.append("Consider simplifying sentences for better readability")
    if structure_issues:
        suggestions.append("Improve document structure with headers and paragraphs")

    return EditResponse(
        original_text=request.text,
        edited_text=request.text,  # TODO: apply fixes
        grammar_issues=grammar_issues,
        readability_score=readability.get("score", 0),
        readability_level=readability.get("level", ""),
        structure_issues=structure_issues,
        suggestions=suggestions,
        word_count=len(request.text.split()),
        char_count=len(request.text),
    )


@app.post("/format", response_model=FormatResponse)
async def format_text(request: FormatRequest) -> FormatResponse:
    """Convert text to different format."""
    result = format_converter.convert(
        request.text,
        request.target_format,
        request.citation_style,
    )
    return FormatResponse(**result)


@app.get("/citation-styles")
async def get_citation_styles():
    """Get supported citation styles."""
    return {
        "styles": [
            {"id": "apa", "name": "APA (American Psychological Association)"},
            {"id": "mla", "name": "MLA (Modern Language Association)"},
            {"id": "chicago", "name": "Chicago Manual of Style"},
            {"id": "ieee", "name": "IEEE (Institute of Electrical and Electronics Engineers)"},
            {"id": "harvard", "name": "Harvard Referencing"},
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8009)
