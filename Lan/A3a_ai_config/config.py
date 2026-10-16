"""Cấu hình đề xuất; không đọc/ghi API key vào file cấu hình."""

import os
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AIConfig(BaseModel):
    """[TỰ ĐỀ XUẤT - CẦN NHÓM CHỐT] Model và giới hạn cho lượt thử."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    provider: str = "openai"
    model: str = "gpt-4.1-mini-2025-04-14"
    base_url: str = "https://api.openai.com/v1"
    temperature: float = Field(default=0.0, ge=0, le=2)
    max_completion_tokens: int = Field(default=1200, ge=1, le=16384)
    timeout_seconds: float = Field(default=30.0, gt=0, le=120)
    group_approved: bool = False

    @field_validator("provider")
    @classmethod
    def supported_provider(cls, value: str) -> str:
        if value != "openai":
            raise ValueError("Chỉ triển khai adapter OpenAI; provider khác cần adapter riêng.")
        return value

    @field_validator("model")
    @classmethod
    def nonempty_model(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Tên model không được rỗng.")
        return value

    @field_validator("base_url")
    @classmethod
    def secure_base_url(cls, value: str) -> str:
        parsed = urlsplit(value)
        if parsed.scheme != "https" or not parsed.hostname:
            raise ValueError("AI base URL phải là HTTPS.")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("Không đặt secret/query/fragment trong AI base URL.")
        return value.rstrip("/")

    @classmethod
    def from_env(cls) -> "AIConfig":
        """Đọc biến môi trường; .env.example chỉ là tài liệu, không tự thực thi."""
        return cls(
            provider=os.getenv("AI_PROVIDER", "openai"),
            model=os.getenv("AI_MODEL", "gpt-4.1-mini-2025-04-14"),
            base_url=os.getenv("AI_BASE_URL", "https://api.openai.com/v1"),
            temperature=float(os.getenv("AI_TEMPERATURE", "0")),
            max_completion_tokens=int(os.getenv("AI_MAX_COMPLETION_TOKENS", "1200")),
            timeout_seconds=float(os.getenv("AI_TIMEOUT_SECONDS", "30")),
            group_approved=os.getenv("AI_GROUP_APPROVED", "0") == "1",
        )
