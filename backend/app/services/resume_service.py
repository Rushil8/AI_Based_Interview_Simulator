import io
import re
import fitz  # PyMuPDF
from typing import Dict, Any


class ResumeParsingError(Exception):
    pass


class ResumeService:
    @staticmethod
    def extract_text_from_pdf_bytes(file_bytes: bytes, filename: str = "resume.pdf") -> Dict[str, Any]:
        """
        Extracts clean text and metadata from PDF bytes using PyMuPDF (fitz).
        Validates content and returns normalized text.
        """
        if not file_bytes or len(file_bytes) == 0:
            raise ResumeParsingError("Uploaded file is empty.")

        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
        except Exception as e:
            raise ResumeParsingError(f"Failed to open PDF document: {str(e)}")

        page_count = len(doc)
        if page_count == 0:
            doc.close()
            raise ResumeParsingError("The uploaded PDF file contains zero pages.")

        extracted_pages = []
        raw_text_parts = []

        for page_num in range(page_count):
            try:
                page = doc[page_num]
                page_text = page.get_text("text")
                if page_text:
                    cleaned_page = ResumeService._clean_text(page_text)
                    if cleaned_page:
                        extracted_pages.append({"page": page_num + 1, "text": cleaned_page})
                        raw_text_parts.append(cleaned_page)
            except Exception as e:
                continue

        doc.close()

        combined_text = "\n\n".join(raw_text_parts).strip()

        if len(combined_text) < 30:
            raise ResumeParsingError(
                "Unable to extract readable text from the PDF. "
                "The document may be scanned as an image or password protected."
            )

        return {
            "filename": filename,
            "page_count": page_count,
            "text": combined_text,
            "pages": extracted_pages,
            "char_count": len(combined_text),
        }

    @staticmethod
    def _clean_text(text: str) -> str:
        """
        Normalizes unicode spaces, strips weird artifacts, and normalizes consecutive newlines.
        """
        if not text:
            return ""
        # Normalize non-breaking spaces and tabs
        text = text.replace("\u00a0", " ").replace("\t", " ")
        # Remove null bytes
        text = text.replace("\x00", "")
        # Normalize line endings
        text = re.sub(r"\r\n|\r", "\n", text)
        # Collapse excessive blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Strip trailing whitespaces on lines
        lines = [line.strip() for line in text.split("\n")]
        return "\n".join(lines).strip()


resume_service = ResumeService()
