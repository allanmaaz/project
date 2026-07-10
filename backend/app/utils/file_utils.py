import io
import struct
from PIL import Image, ImageEnhance, ImageOps
from app.utils.exceptions import UnsupportedFileTypeError


# Magic bytes → MIME type mapping
MAGIC_SIGNATURES: list[tuple[bytes, str]] = [
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"RIFF", "image/webp"),       # RIFF....WEBP
    (b"%PDF", "application/pdf"),
    (b"\x00\x00\x00\x0cftyp", "image/heic"),   # HEIC/HEIF container
    (b"GIF8", "image/gif"),
]

SUPPORTED_MIME_TYPES = {
    "image/jpeg", "image/png", "image/webp",
    "image/heic", "image/heif", "application/pdf",
    # Video uploads
    "video/mp4", "video/webm", "video/quicktime",
    "video/avi", "video/x-msvideo",
}

MIME_TO_EXTENSION = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/heic": "heic",
    "image/heif": "heic",
    "application/pdf": "pdf",
    "video/mp4": "mp4",
    "video/webm": "webm",
    "video/quicktime": "mov",
    "video/avi": "avi",
    "video/x-msvideo": "avi",
}


def detect_mime_type(file_bytes: bytes) -> str:
    """Detect real MIME type from file magic bytes (not extension/header)."""
    header = file_bytes[:16]
    for magic, mime in MAGIC_SIGNATURES:
        if header.startswith(magic):
            # Extra check for WebP: RIFF????WEBP
            if mime == "image/webp":
                if len(file_bytes) >= 12 and file_bytes[8:12] == b"WEBP":
                    return "image/webp"
                continue
            return mime
    raise UnsupportedFileTypeError("unknown")


def validate_file(file_bytes: bytes, mime_type: str, max_bytes: int) -> None:
    """Raises descriptive errors for invalid files."""
    if len(file_bytes) > max_bytes:
        from app.utils.exceptions import UploadTooLargeError
        size_mb = len(file_bytes) / (1024 * 1024)
        limit_mb = max_bytes // (1024 * 1024)
        raise UploadTooLargeError(size_mb, limit_mb)

    if mime_type not in SUPPORTED_MIME_TYPES:
        raise UnsupportedFileTypeError(mime_type)


def preprocess_image(image_bytes: bytes) -> bytes:
    """
    Normalize image for best OCR results:
    - Auto-rotate from EXIF
    - Convert to RGB
    - Enhance contrast
    - Resize if too large (max 4000px longest side)
    Returns processed image as JPEG bytes.
    """
    img = Image.open(io.BytesIO(image_bytes))

    # Auto-rotate from EXIF
    img = ImageOps.exif_transpose(img)

    # Convert to RGB (handles RGBA, palette, etc.)
    if img.mode != "RGB":
        img = img.convert("RGB")

    # Resize if too large
    max_dim = 4000
    if max(img.width, img.height) > max_dim:
        ratio = max_dim / max(img.width, img.height)
        new_size = (int(img.width * ratio), int(img.height * ratio))
        img = img.resize(new_size, Image.LANCZOS)

    # Enhance contrast slightly for better OCR
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.4)

    # Return as JPEG bytes
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=92)
    return out.getvalue()


def generate_thumbnail(image_bytes: bytes, size: tuple = (256, 256)) -> bytes:
    """Generate a JPEG thumbnail of the given image."""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img = ImageOps.exif_transpose(img)
        if img.mode != "RGB":
            img = img.convert("RGB")
        img.thumbnail(size, Image.LANCZOS)
        out = io.BytesIO()
        img.save(out, format="JPEG", quality=85)
        return out.getvalue()
    except Exception:
        return b""


def pdf_first_page_thumbnail(pdf_bytes: bytes) -> bytes:
    """
    Generate thumbnail from first PDF page.
    Returns empty bytes if conversion fails (no pdf2image dependency required).
    """
    try:
        from pypdf import PdfReader
        # pypdf doesn't render pages to images, so we return a placeholder
        # For full PDF thumbnail: would need pdf2image + poppler (optional)
        return b""
    except Exception:
        return b""
