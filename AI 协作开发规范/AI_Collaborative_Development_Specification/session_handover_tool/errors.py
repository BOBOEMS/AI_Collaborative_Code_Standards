"""Structured failures; an unknown acknowledgement is never retried implicitly."""
import re


def redact(message):
    return re.sub(r"(?i)(api[_-]?key|csrf[_-]?token|authorization|bearer|secret|cookie)\s*[:=]\s*\S+",
                  r"\1=[redacted]", str(message))[:1200]


class ToolError(Exception):
    def __init__(self, code, message, *, uncertain=False, details=None):
        super().__init__(redact(message))
        self.code, self.uncertain = code, uncertain
        self.details = details or {}

    def as_dict(self):
        return {"ok": False, "code": self.code, "message": str(self),
                "uncertain": self.uncertain, "details": self.details}
