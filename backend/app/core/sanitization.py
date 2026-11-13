import html
import re
from typing import Optional


def sanitize_text(text: Optional[str]) -> Optional[str]:
    """Sanitize user input string: strip outer whitespace and escape raw HTML entities."""
    if text is None:
        return None
    cleaned = text.strip()
    # Strip HTML tags
    cleaned = re.sub(r"<[^>]*?>", "", cleaned)
    # Escape special characters
    return html.escape(cleaned)


def sanitize_str_field(v: Optional[str]) -> Optional[str]:
    """Pydantic field validator helper for text sanitation."""
    if v is None:
        return None
    return sanitize_text(v)
