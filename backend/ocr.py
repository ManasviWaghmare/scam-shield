"""OCR for WhatsApp screenshot forwards."""
from PIL import Image
import io

def image_to_text(image_bytes: bytes) -> str:
    try:
        import pytesseract
    except ImportError:
        return ""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        # Hindi + Marathi + English
        return pytesseract.image_to_string(img, lang="eng+hin+mar").strip()
    except Exception as e:
        return f"[OCR error: {e}]"
