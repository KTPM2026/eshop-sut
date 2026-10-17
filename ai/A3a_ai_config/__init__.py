"""Giao diện AI dùng chung cho A1 của Lân và L2 của Long."""

from .client import AIClient, AIResponseError
from .config import AIConfig

__all__ = ["AIClient", "AIConfig", "AIResponseError"]
