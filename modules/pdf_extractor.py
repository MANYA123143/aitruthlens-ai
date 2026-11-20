"""
PDF Extraction Module using PyMuPDF (fitz).
Extracts text with page associations, detects scanned/empty documents,
and handles encryption or corruption gracefully.
"""

import io
from typing import Dict, Any, List
import pymupdf


def extract_text_from_pdf(file_bytes: bytes, file_name: str = "document.pdf") -> Dict[str, Any]:
    """
    Extracts text page-by-page from raw PDF bytes.

    Returns:
        dict: {
            "success": bool,
            "error": Optional[str],
            "total_pages": int,
            "pages": List[Dict[str, Any]], # [{"page_number": int, "text": str, "char_count": int}]
            "full_text": str,
            "is_scanned": bool,
            "total_chars": int
        }
    """
    if not file_bytes or len(file_bytes) == 0:
        return {
            "success": False,
            "error": "The uploaded file is empty (0 bytes). Please upload a valid PDF document.",
            "total_pages": 0,
            "pages": [],
            "full_text": "",
            "is_scanned": False,
            "total_chars": 0
        }

    try:
        # Load PDF from memory stream
        stream = io.BytesIO(file_bytes)
        doc = pymupdf.open(stream=stream, filetype="pdf")
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to open PDF document. The file might be corrupted or in an unsupported format. Error: {str(e)}",
            "total_pages": 0,
            "pages": [],
            "full_text": "",
            "is_scanned": False,
            "total_chars": 0
        }

    try:
        if doc.is_encrypted:
            return {
                "success": False,
                "error": "The uploaded PDF is password-protected. Please decrypt or unlock the document before uploading.",
                "total_pages": len(doc),
                "pages": [],
                "full_text": "",
                "is_scanned": False,
                "total_chars": 0
            }

        total_pages = len(doc)
        if total_pages == 0:
            return {
                "success": False,
                "error": "The PDF document contains no pages.",
                "total_pages": 0,
                "pages": [],
                "full_text": "",
                "is_scanned": False,
                "total_chars": 0
            }

        pages_data: List[Dict[str, Any]] = []
        full_text_list: List[str] = []
        total_chars = 0

        for page_idx in range(total_pages):
            page = doc[page_idx]
            page_text = page.get_text("text").strip()
            char_count = len(page_text)
            total_chars += char_count

            pages_data.append({
                "page_number": page_idx + 1,
                "text": page_text,
                "char_count": char_count
            })
            if page_text:
                full_text_list.append(f"--- PAGE {page_idx + 1} ---\n{page_text}")

        full_text = "\n\n".join(full_text_list)
        
        # Scanned PDF detection: average characters per page < 40
        is_scanned = (total_chars / total_pages) < 40 if total_pages > 0 else True

        if total_chars == 0:
            return {
                "success": True,
                "warning": "No digital text could be extracted from this PDF. It appears to be an image-only scanned document or empty. OCR is required to read scanned content.",
                "total_pages": total_pages,
                "pages": pages_data,
                "full_text": "",
                "is_scanned": True,
                "total_chars": 0
            }

        return {
            "success": True,
            "error": None,
            "total_pages": total_pages,
            "pages": pages_data,
            "full_text": full_text,
            "is_scanned": is_scanned,
            "total_chars": total_chars
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"An unexpected error occurred while parsing the PDF: {str(e)}",
            "total_pages": 0,
            "pages": [],
            "full_text": "",
            "is_scanned": False,
            "total_chars": 0
        }
    finally:
        try:
            doc.close()
        except Exception:
            pass
