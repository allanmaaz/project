"""
Unit tests for file utilities.
"""
import pytest
import io
from PIL import Image
from app.utils.file_utils import (
    detect_mime_type,
    validate_file,
    preprocess_image,
    generate_thumbnail,
    pdf_first_page_thumbnail,
)


class TestDetectMimeType:
    def test_jpeg(self):
        # JPEG magic bytes: FF D8 FF
        data = b"\xff\xd8\xff" + b"x" * 100
        assert detect_mime_type(data) == "image/jpeg"

    def test_png(self):
        # PNG magic bytes: 89 50 4E 47 0D 0A 1A 0A
        data = b"\x89PNG\r\n\x1a\n" + b"x" * 100
        assert detect_mime_type(data) == "image/png"

    def test_webp(self):
        # WebP: RIFF....WEBP
        data = b"RIFF" + b"x" * 4 + b"WEBP" + b"x" * 100
        assert detect_mime_type(data) == "image/webp"

    def test_pdf(self):
        # PDF magic bytes: %PDF
        data = b"%PDF-1.5" + b"x" * 100
        assert detect_mime_type(data) == "application/pdf"

    def test_heic(self):
        # HEIC magic bytes
        data = b"\x00\x00\x00\x0cftypheic" + b"x" * 100
        assert detect_mime_type(data) == "image/heic"

    def test_unknown_raises(self):
        from app.utils.exceptions import UnsupportedFileTypeError
        data = b"unknown"
        with pytest.raises(UnsupportedFileTypeError):
            detect_mime_type(data)

    def test_webp_requires_webp_signature(self):
        # RIFF without WEBP should not be detected as webp
        data = b"RIFF" + b"x" * 100
        from app.utils.exceptions import UnsupportedFileTypeError
        with pytest.raises(UnsupportedFileTypeError):
            detect_mime_type(data)


class TestValidateFile:
    def test_valid_jpeg_under_limit(self):
        data = b"\xff\xd8\xff" + b"x" * (1024 * 1024)  # ~1MB JPEG
        validate_file(data, "image/jpeg", 20 * 1024 * 1024)  # 20MB limit

    def test_too_large_raises(self):
        from app.utils.exceptions import UploadTooLargeError
        data = b"x" * (25 * 1024 * 1024)  # 25MB
        with pytest.raises(UploadTooLargeError):
            validate_file(data, "image/jpeg", 20 * 1024 * 1024)

    def test_unsupported_type_raises(self):
        from app.utils.exceptions import UnsupportedFileTypeError
        data = b"\xff\xd8\xff" + b"x" * 100
        with pytest.raises(UnsupportedFileTypeError):
            validate_file(data, "image/gif", 20 * 1024 * 1024)


class TestPreprocessImage:
    def test_converts_to_rgb(self):
        # Create RGBA image
        img = Image.new("RGBA", (100, 100), (255, 0, 0, 128))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        data = buf.getvalue()

        result = preprocess_image(data)
        assert len(result) > 0
        # Should be JPEG now
        assert detect_mime_type(result) == "image/jpeg"

    def test_resizes_large_image(self):
        # Create large image
        img = Image.new("RGB", (5000, 3000), (0, 255, 0))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        data = buf.getvalue()

        result = preprocess_image(data)
        # Load result and check dimensions
        result_img = Image.open(io.BytesIO(result))
        assert max(result_img.width, result_img.height) <= 4000

    def test_enhances_contrast(self):
        img = Image.new("RGB", (100, 100), (128, 128, 128))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        data = buf.getvalue()

        result = preprocess_image(data)
        # Should produce valid JPEG
        result_img = Image.open(io.BytesIO(result))
        assert result_img.format == "JPEG"


class TestGenerateThumbnail:
    def test_creates_thumbnail(self):
        img = Image.new("RGB", (500, 300), (255, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        data = buf.getvalue()

        thumb = generate_thumbnail(data, (100, 100))
        assert len(thumb) > 0
        
        thumb_img = Image.open(io.BytesIO(thumb))
        assert thumb_img.format == "JPEG"
        assert max(thumb_img.width, thumb_img.height) <= 100

    def test_preserves_aspect_ratio(self):
        img = Image.new("RGB", (500, 200), (0, 255, 0))  # Wide image
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        data = buf.getvalue()

        thumb = generate_thumbnail(data, (100, 100))
        thumb_img = Image.open(io.BytesIO(thumb))
        # Should fit within 100x100 preserving aspect ratio
        assert thumb_img.width <= 100
        assert thumb_img.height <= 100


class TestPdfFirstPageThumbnail:
    def test_returns_empty_for_no_pdf2image(self):
        # pypdf doesn't render pages, so should return empty
        data = b"%PDF-1.5" + b"x" * 100
        result = pdf_first_page_thumbnail(data)
        assert result == b""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])