from typing import Any, List


def extract_text_content(content: Any) -> str:
    """
    Handles:
    - string content
    - AI SDK format: [{ type: 'text', text: '...' }]
    """

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        text_parts: List[str] = [
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and part.get("type") == "text"
        ]
        return "\n".join(p for p in text_parts if p).strip()

    return ""

