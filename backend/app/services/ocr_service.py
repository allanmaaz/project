"""
OCR Service — extracts text from images and PDFs.
Primary: Tesseract (free, local, no API key needed)
Fallback for complex images: Gemini Vision (free tier)
"""
import io
import base64
from dataclasses import dataclass
from app.utils.file_utils import preprocess_image
from app.utils.text_utils import clean_text


@dataclass
class OCRResult:
    text: str
    confidence: float
    source: str    # "tesseract" | "gemini_vision" | "pdf_text"
    page_count: int = 1


class OCRService:
    def __init__(self, gemini_model=None):
        self.gemini = gemini_model  # injected from LLMService if available

    async def extract(self, file_bytes: bytes, mime_type: str) -> OCRResult:
        """Main entry point — routes to correct extractor."""
        if mime_type == "application/pdf":
            return await self._extract_pdf(file_bytes)
        return await self._extract_image(file_bytes, mime_type)

    async def _extract_image(self, image_bytes: bytes, mime_type: str) -> OCRResult:
        """Extract text from image using Tesseract, with Gemini Vision fallback."""
        # Pre-process image for better OCR
        try:
            processed = preprocess_image(image_bytes)
        except Exception:
            processed = image_bytes

        # PRIMARY: Tesseract (free, local)
        try:
            import pytesseract
            from PIL import Image
            img = Image.open(io.BytesIO(processed))
            raw_text = pytesseract.image_to_string(img, timeout=30)
            text = clean_text(raw_text)

            # If Tesseract got meaningful text, return it
            if len(text.strip()) > 30:
                return OCRResult(text=text, confidence=0.85, source="tesseract")
        except Exception:
            pass

        # FALLBACK: Gemini Vision (free tier, handles complex images better)
        if self.gemini:
            try:
                return await self._gemini_vision_ocr(processed, mime_type)
            except Exception:
                pass

        # Last resort: return empty if both fail
        return OCRResult(text="", confidence=0.0, source="failed")

    async def _extract_pdf(self, pdf_bytes: bytes) -> OCRResult:
        """Extract text from PDF — text layer first, then OCR pages."""
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(pdf_bytes))
            pages = []
            for page in reader.pages:
                page_text = page.extract_text() or ""
                pages.append(page_text)

            combined = "\n\n--- Page Break ---\n\n".join(pages)
            combined = clean_text(combined)

            # If meaningful text layer exists, use it
            if len(combined.strip()) > 100:
                return OCRResult(
                    text=combined,
                    confidence=0.99,
                    source="pdf_text",
                    page_count=len(reader.pages),
                )
        except Exception:
            pass

        # PDF has no text layer — OCR the first page using Gemini Vision
        if self.gemini:
            try:
                return await self._gemini_vision_ocr(pdf_bytes, "application/pdf")
            except Exception:
                pass

        return OCRResult(text="", confidence=0.0, source="failed")

    async def _gemini_vision_ocr(self, image_bytes: bytes, mime_type: str) -> OCRResult:
        """Use Gemini Vision to extract text from complex images (free tier)."""
        import google.generativeai as genai
        from PIL import Image
        import asyncio

        # Convert to PIL Image for Gemini
        if mime_type == "application/pdf":
            raise ValueError("PDF passed to vision OCR")

        img = Image.open(io.BytesIO(image_bytes))
        
        # Instantiate a clean model without JSON constraint for OCR
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = await asyncio.to_thread(
            model.generate_content,
            [
                "Extract ALL text from this image exactly as it appears. "
                "Preserve line breaks and structure. Output ONLY the extracted text, nothing else.",
                img
            ]
        )
        text = clean_text(response.text or "")
        return OCRResult(text=text, confidence=0.92, source="gemini_vision")
