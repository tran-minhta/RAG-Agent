"""
RAG-ALL: Document Processing Pipeline
Orchestrates the full document processing flow:
  File → Detect Type → Route to Extractor → Clean → Markdown

This pipeline is the core of document ingestion.
"""

from pathlib import Path
from shared.utils.logger import document_logger as logger


class DocumentPipeline:
    """
    Main document processing pipeline.

    Flow:
      1. Detect file type (Magika)
      2. Route to appropriate extractor
      3. Extract content
      4. Clean and post-process
      5. Return structured result
    """

    def __init__(self, detector, extractors: dict):
        """
        Args:
            detector: File type detector (MagikaDetector)
            extractors: Dict mapping content_type → extractor instance
        """
        self.detector = detector
        self.extractors = extractors

    async def process(self, file_path: str, doc_id: str, filename: str = "") -> dict:
        """
        Process a document through the full pipeline.

        Args:
            file_path: Path to the file
            doc_id: Unique document ID
            filename: Original filename (optional)

        Returns:
            dict với markdown_content, metadata, etc.
        """
        logger.info(f"Pipeline processing: {file_path} (id={doc_id})")

        # Validate file exists
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Step 1: Detect file type
        logger.info("Step 1: Detecting file type...")
        detection = await self.detector.detect(file_path)
        content_type = detection.get("content_type", "unknown")
        logger.info(f"  Detected: {content_type} (confidence: {detection.get('confidence', 0):.2f})")

        # Step 2: Select extractor
        logger.info("Step 2: Selecting extractor...")
        extractor = self._select_extractor(content_type)
        if extractor is None:
            raise ValueError(f"No extractor available for type: {content_type}")

        # Step 3: Extract content
        logger.info("Step 3: Extracting content...")
        result = await extractor.extract(file_path, doc_id)

        # Step 4: Clean and post-process
        logger.info("Step 4: Post-processing...")
        cleaned_content = self._clean_markdown(result.get("markdown_content", ""))

        # Step 5: Build result
        metadata = result.get("metadata", {})
        metadata.update({
            "doc_id": doc_id,
            "filename": filename or path.name,
            "content_type": content_type,
            "file_size": path.stat().st_size,
            "detection_confidence": detection.get("confidence", 0),
            "detection_detector": detection.get("detector", "unknown"),
        })

        logger.info(f"Pipeline complete: {len(cleaned_content)} chars extracted")

        return {
            "doc_id": doc_id,
            "doc_type": content_type,
            "markdown_content": cleaned_content,
            "metadata": metadata,
            "images": result.get("images", []),
            "tables": result.get("tables", []),
            "formulas": result.get("formulas", []),
            "success": True,
            "message": f"Successfully extracted {content_type} document",
        }

    def _select_extractor(self, content_type: str):
        """
        Select appropriate extractor based on content type.

        Mapping:
          pdf → MinerUExtractor
          docx/pptx/xlsx → MarkItDownExtractor
          html/txt/markdown → MarkItDownExtractor
        """
        # Direct match
        if content_type in self.extractors:
            return self.extractors[content_type]

        # Fuzzy match (e.g., "msword" → "docx")
        type_mapping = {
            "pdf": "pdf",
            "docx": "docx",
            "doc": "docx",
            "pptx": "pptx",
            "ppt": "pptx",
            "xlsx": "xlsx",
            "xls": "xlsx",
            "html": "html",
            "htm": "html",
            "txt": "txt",
            "markdown": "markdown",
            "md": "markdown",
            "csv": "txt",
            "json": "txt",
            "xml": "txt",
        }

        mapped_type = type_mapping.get(content_type.lower())
        if mapped_type and mapped_type in self.extractors:
            return self.extractors[mapped_type]

        # Default to MarkItDown for unknown types
        if "txt" in self.extractors:
            logger.warning(f"No specific extractor for '{content_type}', using txt fallback")
            return self.extractors.get("txt")

        return None

    def _clean_markdown(self, content: str) -> str:
        """
        Clean và post-process markdown content.

        Removes:
          - Excessive whitespace
          - Empty lines (more than 2 consecutive)
          - Page break artifacts
          - Header/footer noise
        """
        if not content:
            return ""

        import re

        # Remove excessive blank lines (keep max 2)
        content = re.sub(r'\n{3,}', '\n\n', content)

        # Remove trailing whitespace on lines
        content = re.sub(r'[ \t]+$', '', content, flags=re.MULTILINE)

        # Remove page break markers
        content = re.sub(r'---\s*\n\s*---', '\n', content)

        # Remove common header/footer patterns
        content = re.sub(r'^\d+\s*$', '', content, flags=re.MULTILINE)  # Page numbers

        # Clean up markdown headers (ensure single space after #)
        content = re.sub(r'^(#{1,6})\s*(?!\s)', r'\1 ', content, flags=re.MULTILINE)

        return content.strip()
