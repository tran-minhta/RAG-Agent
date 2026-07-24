"""
RAG-ALL: MarkItDown Extractor
Trích xuất nội dung từ DOCX/PPTX/XLSX/HTML sang Markdown.

MarkItDown là tool của Microsoft, hỗ trợ 100+ file formats:
  - Word (DOCX/DOC)
  - PowerPoint (PPTX/PPT)
  - Excel (XLSX/XLS)
  - HTML/HTM
  - Images (OCR optional)
  - PDF (as fallback)
  - And many more

GitHub: https://github.com/microsoft/markitdown (168k+ stars)
"""

from pathlib import Path
from shared.utils.logger import document_logger as logger


class MarkItDownExtractor:
    """
    Multi-format extractor sử dụng Microsoft MarkItDown.

    Converts various file formats to clean Markdown
    suitable for LLM processing and RAG pipelines.
    """

    def __init__(self):
        self._md = None
        self._initialized = False

    def _ensure_initialized(self):
        """Lazy init MarkItDown."""
        if self._initialized:
            return

        try:
            from markitdown import MarkItDown
            self._md = MarkItDown()
            self._initialized = True
            logger.info("MarkItDown initialized successfully")
        except ImportError:
            logger.warning("MarkItDown not installed. Using fallback extraction.")
            self._initialized = True

    async def extract(self, file_path: str, doc_id: str) -> dict:
        """
        Extract content to Markdown.

        Args:
            file_path: Path to document file
            doc_id: Document ID

        Returns:
            dict với markdown_content, metadata
        """
        self._ensure_initialized()

        logger.info(f"MarkItDown extracting: {file_path}")

        # Use MarkItDown if available
        if self._md is not None:
            try:
                result = self._md.convert(file_path)
                return {
                    "markdown_content": result.text_content or "",
                    "images": [],
                    "tables": [],
                    "formulas": [],
                    "metadata": {
                        "source_file": file_path,
                        "extractor": "markitdown",
                        "content_length": len(result.text_content or ""),
                    },
                }
            except Exception as e:
                logger.error(f"MarkItDown extraction error: {e}")

        # Fallback extraction
        return await self._fallback_extract(file_path, doc_id)

    async def _fallback_extract(self, file_path: str, doc_id: str) -> dict:
        """
        Fallback extraction dựa trên file type.
        Đọc text trực tiếp từ file.
        """
        path = Path(file_path)
        ext = path.suffix.lower()

        try:
            # Try reading as text
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            return {
                "markdown_content": content,
                "images": [],
                "tables": [],
                "formulas": [],
                "metadata": {
                    "source_file": file_path,
                    "extractor": "text_fallback",
                    "extension": ext,
                },
            }
        except Exception as e:
            logger.error(f"Fallback extraction error: {e}")
            return {
                "markdown_content": f"[Error: Cannot extract {ext} file. Please install markitdown.]",
                "images": [],
                "tables": [],
                "formulas": [],
                "metadata": {
                    "source_file": file_path,
                    "extractor": "none",
                    "error": str(e),
                },
            }
