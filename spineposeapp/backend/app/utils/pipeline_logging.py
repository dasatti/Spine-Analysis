import structlog.contextvars

PIPELINE_CONTEXT_KEYS = ("scan_id", "doctor_id", "detector_model")


def bind_pipeline_context(
    *,
    scan_id: str,
    doctor_id: str | None,
    detector_model: str,
) -> None:
    structlog.contextvars.bind_contextvars(
        scan_id=scan_id,
        doctor_id=doctor_id,
        detector_model=detector_model,
    )


def clear_pipeline_context() -> None:
    structlog.contextvars.unbind_contextvars(*PIPELINE_CONTEXT_KEYS)
