"""[TỰ ĐỀ XUẤT - CẦN NHÓM CHỐT] Hợp đồng JSON, kiểm tra bằng Pydantic."""

from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictContract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Alert(StrictContract):
    alert_id: str = Field(min_length=1, max_length=200)
    name: str = Field(min_length=1, max_length=1000)
    risk: Literal["High", "Medium", "Low", "Informational", "Unknown"]
    url: str = Field(min_length=1, max_length=8000)
    param: str = Field(max_length=1000)
    evidence: str = Field(max_length=16000)
    cweid: str | None

    @field_validator("url")
    @classmethod
    def absolute_http_url(cls, value: str) -> str:
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("Alert cần URL HTTP(S) tuyệt đối.")
        if parsed.username or parsed.password:
            raise ValueError("URL không được chứa thông tin đăng nhập.")
        return value


class TriageSuggestion(StrictContract):
    alert_id: str = Field(min_length=1, max_length=200)
    is_real: bool | None
    priority: Literal["P1", "P2", "P3", "P4"]
    reason: str = Field(min_length=1, max_length=3000)
    confidence: float = Field(ge=0, le=1)
    trang_thai_bang_chung: Literal[
        "can_xac_minh", "co_bang_chung_ho_tro", "khong_du_bang_chung"
    ]


class PreviousAttempt(StrictContract):
    payload: str = Field(max_length=1024)
    response_code: int = Field(ge=100, le=599)
    blocked: bool
    effect_observed: bool | None


class PayloadRequest(StrictContract):
    target_url: str = Field(min_length=1, max_length=8000)
    vulnerability_type: Literal["SQLi", "XSS"]
    previous_attempts: list[PreviousAttempt] = Field(max_length=50)
    remaining_requests: int = Field(ge=0, le=1000)

    @field_validator("target_url")
    @classmethod
    def local_lab_only(cls, value: str) -> str:
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or parsed.hostname not in {
            "localhost", "127.0.0.1", "::1"
        }:
            raise ValueError("Payload chỉ dành cho lab loopback được phép.")
        if parsed.username or parsed.password:
            raise ValueError("Không đặt thông tin đăng nhập trong URL.")
        return value


class PayloadSuggestion(StrictContract):
    payload: str = Field(max_length=1024)
    reason: str = Field(min_length=1, max_length=3000)
    should_stop: bool


def json_contracts() -> dict:
    """Xuất schema từ model để JSON và validator không lệch nhau."""
    return {
        "schema_version": "lan-ai-v1-proposed",
        "group_approved": False,
        "assumption_notice": "TỰ ĐỀ XUẤT - CẦN NHÓM CHỐT",
        "alert_input": Alert.model_json_schema(),
        "triage_output": TriageSuggestion.model_json_schema(),
        "payload_input": PayloadRequest.model_json_schema(),
        "payload_output": PayloadSuggestion.model_json_schema(),
    }
