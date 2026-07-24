"""
RAG-ALL: Magika File Type Detector
Sử dụng Google Magika AI để detect file type chính xác (99% accuracy).

Magika là một tool AI-powered do Google develop, sử dụng deep learning
để detect file content type thay vì dựa vào file extension.
"""

from pathlib import Path
from shared.utils.logger import document_logger as logger


class MagikaDetector:
    """
    File type detector sử dụng Google Magika AI.

    Hỗ trợ 200+ content types bao gồm:
      - PDF, DOCX, PPTX, XLSX
      - Images (JPG, PNG, SVG)
      - Code files (Python, JS, etc.)
      - Text formats (TXT, MD, HTML)
      - And many more
    """

    def __init__(self):
        self._magika = None
        self._initialized = False

    async def _ensure_initialized(self):
        """Lazy init Magika (tránh load model khi không cần)."""
        if self._initialized:
            return

        try:
            import magika
            self._magika = magika.Magika()
            self._initialized = True
            logger.info("Magika detector initialized successfully")
        except ImportError:
            logger.warning("Magika not installed. Using fallback detection.")
            self._initialized = True

    async def detect(self, file_path: str) -> dict:
        """
        Detect file type.

        Args:
            file_path: Đường dẫn đến file

        Returns:
            dict với các fields:
              - mime_type: MIME type (e.g., "application/pdf")
              - content_type: Content type name (e.g., "pdf")
              - extension: Detected extension
              - confidence: Confidence score (0-1)
              - is_text: Whether file is text-based
        """
        await self._ensure_initialized()

        path = Path(file_path)
        if not path.exists():
            return self._fallback_detect(file_path)

        # Use Magika if available
        if self._magika is not None:
            try:
                result = self._magika.identify_file(str(path))
                detected = result.output

                # Magika returns a list of predictions, take the best one
                if detected:
                    best = detected[0]
                    return {
                        "mime_type": best.mime_type or "application/octet-stream",
                        "content_type": best.label or "unknown",
                        "extension": best.mime_type.split("/")[-1] if best.mime_type else "",
                        "confidence": best.score if hasattr(best, 'score') else 0.9,
                        "is_text": best.is_text if hasattr(best, 'is_text') else False,
                        "detector": "magika",
                    }
            except Exception as e:
                logger.error(f"Magika detection error: {e}")

        # Fallback to extension-based detection
        return self._fallback_detect(file_path)

    def _fallback_detect(self, file_path: str) -> dict:
        """
        Fallback detection dựa trên file extension.
        Dùng khi Magika không khả dụng.
        """
        path = Path(file_path)
        ext = path.suffix.lower()

        # Mapping extensions to content types
        ext_map = {
            ".pdf": ("application/pdf", "pdf"),
            ".docx": ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", "docx"),
            ".doc": ("application/msword", "doc"),
            ".pptx": ("application/vnd.openxmlformats-officedocument.presentationml.presentation", "pptx"),
            ".xlsx": ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "xlsx"),
            ".txt": ("text/plain", "txt"),
            ".md": ("text/markdown", "markdown"),
            ".html": ("text/html", "html"),
            ".htm": ("text/html", "html"),
            ".csv": ("text/csv", "csv"),
            ".json": ("application/json", "json"),
            ".xml": ("application/xml", "xml"),
            ".jpg": ("image/jpeg", "image"),
            ".jpeg": ("image/jpeg", "image"),
            ".png": ("image/png", "image"),
            ".gif": ("image/gif", "image"),
            ".svg": ("image/svg+xml", "image"),
            ".py": ("text/x-python", "code"),
            ".js": ("text/javascript", "code"),
            ".ts": ("text/typescript", "code"),
        }

        mime_type, content_type = ext_map.get(ext, ("application/octet-stream", "unknown"))
        is_text = mime_type.startswith("text/") or content_type in ("markdown", "csv", "json", "xml", "code")

        return {
            "mime_type": mime_type,
            "content_type": content_type,
            "extension": ext.lstrip("."),
            "confidence": 0.7,  # Lower confidence for fallback
            "is_text": is_text,
            "detector": "fallback",
        }
