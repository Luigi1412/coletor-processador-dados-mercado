"""Exceções tipadas do pipeline."""

from __future__ import annotations


class PipelineError(Exception):
    """Erro de negócio do pipeline com mensagem compreensível."""

    def __init__(self, message: str, *, code: str = "pipeline_error", details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


class ValidationError(PipelineError):
    def __init__(self, message: str, *, details: dict | None = None):
        super().__init__(message, code="validation_error", details=details)


class InsufficientDataError(PipelineError):
    def __init__(self, message: str, *, details: dict | None = None):
        super().__init__(message, code="insufficient_data", details=details)


class PartialFailureError(PipelineError):
    """Falha parcial: alguns ativos indisponíveis e allow_partial=False."""

    def __init__(self, message: str, *, failed: list[str], available: list[str]):
        super().__init__(
            message,
            code="partial_failure",
            details={"failed": failed, "available": available},
        )
        self.failed = failed
        self.available = available


class ProviderError(PipelineError):
    def __init__(self, message: str, *, details: dict | None = None):
        super().__init__(message, code="provider_error", details=details)
