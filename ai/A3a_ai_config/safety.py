"""Che một số dạng secret phổ biến; vẫn cần người rà dữ liệu trước khi gửi AI."""

import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


SECRET_KEY = re.compile(
    r"^(authorization|proxy-authorization|cookie|set-cookie|password|passwd|"
    r"api[_-]?key|access[_-]?token|refresh[_-]?token|reset[_-]?token|token|secret)$",
    re.IGNORECASE,
)
AUTH_HEADER = re.compile(r"(?im)((?:proxy-)?authorization\s*:\s*)[^\r\n]+")
COOKIE_HEADER = re.compile(r"(?im)((?:set-)?cookie\s*:\s*)[^\r\n]+")
ASSIGNMENT = re.compile(
    r"(?i)((?:password|passwd|api[_-]?key|access[_-]?token|refresh[_-]?token|"
    r"reset[_-]?token|token|secret)[\"']?\s*[:=]\s*[\"']?)[^\s&\"',;<>}]+"
)
JWT = re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b")
API_KEY = re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b")


def redact(value):
    """Che đệ quy theo key và best-effort cho HTTP/text, không bảo đảm xóa mọi PII."""
    if isinstance(value, dict):
        return {key: "[REDACTED]" if SECRET_KEY.fullmatch(str(key)) else redact(item)
                for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    if not isinstance(value, str):
        return value
    text = AUTH_HEADER.sub(r"\1[REDACTED]", value)
    text = COOKIE_HEADER.sub(r"\1[REDACTED]", text)
    text = ASSIGNMENT.sub(r"\1[REDACTED]", text)
    text = JWT.sub("[REDACTED]", text)
    return API_KEY.sub("[REDACTED]", text)


def redact_url(value: str) -> str:
    """Che tham số nhạy cảm sau khi URL-decode query."""
    parsed = urlsplit(value)
    query = [(key, "[REDACTED]" if SECRET_KEY.fullmatch(key) else redact(item))
             for key, item in parse_qsl(parsed.query, keep_blank_values=True)]
    return urlunsplit(parsed._replace(query=urlencode(query)))
