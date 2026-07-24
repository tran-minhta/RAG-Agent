"""
RAG-ALL: MinerU PDF Extractor
Trích xuất nội dung PDF sang Markdown sử dụng MinerU.

MinerU là tool open-source từ OpenDataLab, hỗ trợ:
  - OCR cho scanned PDFs
  - Bảng biểu (table recognition)
  - Công thức toán (formula recognition)
  - Layout detection
  - Image extraction

GitHub: https://github.com/opendatalab/MinerU
"""

import subprocess
import json
from pathlib import Path
from shared.utils.logger import document_logger as logger


class MinerUExtractor:
    """
    PDF extractor sử dụng MinerU.

    Pipeline:
      1. Check if MinerU is available (pip install mineru)
      2. Run MinerU CLI to convert PDF → Markdown
      3. Parse output and return structured content
    """

    def __init__(self):
        self._available = None  # Lazy check

    def _check_available(self) -> bool:
        """Kiểm tra MinerU có được install không."""
        if self._available is not None:
            return self._available

        try:
            result = subprocess.run(
                ["magic-pdf", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            self._available = result.returncode == 0
            if self._available:
                logger.info("MinerU (magic-pdf) is available")
            else:
                logger.warning("MinerU (magic-pdf) not found, using fallback")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self._available = False
            logger.warning("MinerU not available, using fallback extraction")

        return self._available

    async def extract(self, file_path: str, doc_id: str) -> dict:
        """
        Extract PDF to Markdown.

        Args:
            file_path: Path to PDF file
            doc_id: Document ID for tracking

        Returns:
            dict với:
              - markdown_content: Extracted markdown text
              - images: List of extracted images info
              - tables: List of extracted tables
              - formulas: List of extracted formulas
              - metadata: Page count, language, etc.
        """
        logger.info(f"MinerU extracting: {file_path}")

        if not self._check_available():
            return await self._fallback_extract(file_path, doc_id)

        try:
            return await self._extract_with_mineru(file_path, doc_id)
        except Exception as e:
            logger.error(f"MinerU extraction error: {e}")
            return await self._fallback_extract(file_path, doc_id)

    async def _extract_with_mineru(self, file_path: str, doc_id: str) -> dict:
        """Extract using MinerU CLI."""
        output_dir = f"data/cache/mineru_{doc_id}"
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Run MinerU
        # magic-pdf -p <pdf_path> -o <output_dir> -m auto
        cmd = [
            "magic-pdf",
            "-p", file_path,
            "-o", output_dir,
            "-m", "auto",  # Auto mode: detect text vs scanned
        ]

        logger.info(f"Running: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutes timeout
        )

        if result.returncode != 0:
            logger.error(f"MinerU failed: {result.stderr}")
            return await self._fallback_extract(file_path, doc_id)

        # Parse MinerU output
        return self._parse_mineru_output(output_dir, file_path, doc_id)

    def _parse_mineru_output(self, output_dir: str, file_path: str, doc_id: str) -> dict:
        """Parse MinerU output directory."""
        output_path = Path(output_dir)
        md_files = list(output_path.rglob("*.md"))
        image_files = list(output_path.rglob("*.png")) + list(output_path.rglob("*.jpg"))

        # Read all markdown files
        markdown_content = ""
        for md_file in md_files:
            with open(md_file, "r", encoding="utf-8") as f:
                markdown_content += f.read() + "\n\n"

        # Collect image info
        images = []
        for img in image_files:
            images.append({
                "path": str(img),
                "filename": img.name,
                "size": img.stat().st_size,
            })

        # Estimate page count from markdown (rough)
        page_count = markdown_content.count("---\n") + 1

        return {
            "markdown_content": markdown_content.strip(),
            "images": images,
            "tables": [],  # MinerU embeds tables in markdown
            "formulas": [],  # MinerU converts formulas to LaTeX
            "metadata": {
                "source_file": file_path,
                "output_dir": output_dir,
                "page_count": page_count,
                "image_count": len(images),
                "extractor": "mineru",
            },
        }

    async def _fallback_extract(self, file_path: str, doc_id: str) -> dict:
        """
        Fallback extraction khi MinerU không khả dụng.
        Sử dụng PyMuPDF hoặc pdfminer.
        """
        logger.info(f"Using fallback extraction for: {file_path}")

        # Try PyMuPDF first
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            markdown_content = ""
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                if text.strip():
                    markdown_content += f"## Page {page_num + 1}\n\n{text}\n\n"
            doc.close()

            return {
                "markdown_content": markdown_content.strip(),
                "images": [],
                "tables": [],
                "formulas": [],
                "metadata": {
                    "source_file": file_path,
                    "page_count": len(doc),
                    "extractor": "pymupdf_fallback",
                },
            }
        except ImportError:
            pass

        # Try pdfminer
        try:
            from pdfminer.high_level import extract_text
            text = extract_text(file_path)

            return {
                "markdown_content": text.strip(),
                "images": [],
                "tables": [],
                "formulas": [],
                "metadata": {
                    "source_file": file_path,
                    "extractor": "pdfminer_fallback",
                },
            }
        except ImportError:
            pass

        # Last resort: return error
        return {
            "markdown_content": f"[Error: Cannot extract PDF. Please install MinerU or PyMuPDF.]",
            "images": [],
            "tables": [],
            "formulas": [],
            "metadata": {
                "source_file": file_path,
                "extractor": "none",
                "error": "No PDF extraction library available",
            },
        }
