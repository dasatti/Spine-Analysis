import json
import shutil
import tempfile
import uuid
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import structlog
from celery import Celery
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.models.patient import Patient, RiskLevel
from app.models.scan import Scan, ScanStatus
from app.pipeline.keypoint_normalizer import KeypointNormalizer
from app.pipeline.loader import get_detector
from app.pipeline.metric_engine import CalibrationData, compute_all, derive_overall_risk
from app.pipeline.reconstructor_3d import Reconstructor3D
from app.pipeline.spine_curve_model import SpineCurveModel
from app.services.storage_service import storage_service
from app.utils.logging_config import configure_logging
from app.utils.pipeline_logging import bind_pipeline_context, clear_pipeline_context

configure_logging(settings.log_level)
logger = structlog.get_logger(__name__)

celery_app = Celery(
    "spinepose",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

_sync_engine = None
_SessionLocal: sessionmaker[Session] | None = None
_detector = None

RISK_RANK = {
    RiskLevel.normal: 0,
    RiskLevel.monitor: 1,
    RiskLevel.elevated: 2,
}


def _sync_database_url() -> str:
    url = settings.database_url
    if "+asyncpg" in url:
        return url.replace("+asyncpg", "+psycopg2")
    return url


def get_sync_session() -> Session:
    global _sync_engine, _SessionLocal
    if _SessionLocal is None:
        _sync_engine = create_engine(_sync_database_url(), pool_pre_ping=True)
        _SessionLocal = sessionmaker(bind=_sync_engine, expire_on_commit=False)
    return _SessionLocal()


def _get_detector():
    global _detector
    if _detector is None:
        _detector = get_detector()
    return _detector


def _update_scan(session: Session, scan: Scan, **fields) -> None:
    for key, value in fields.items():
        setattr(scan, key, value)
    session.commit()


def _download_frames(prefix: str, temp_dir: Path) -> dict[str, str]:
    frame_paths: dict[str, str] = {}
    for view in ("front", "side", "back", "adams", "face"):
        key = storage_service.find_frame_key(prefix, view)
        if key is None:
            if view != "face":
                logger.warning("Missing required frame", view=view, prefix=prefix)
            continue
        ext = key.rsplit(".", 1)[-1]
        local_path = temp_dir / f"{view}.{ext}"
        storage_service._client.download_file(storage_service._bucket, key, str(local_path))
        frame_paths[view] = str(local_path)
    return frame_paths


def _keypoints_to_json(keypoints: list) -> list[dict]:
    return [asdict(kp) for kp in keypoints]


def _worsen_patient_risk(patient: Patient, new_risk_value: str) -> None:
    new_risk = RiskLevel(new_risk_value)
    if RISK_RANK[new_risk] > RISK_RANK[patient.risk_level]:
        patient.risk_level = new_risk


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def process_scan(self, scan_id: str) -> None:
    """Run the full scan processing pipeline for a queued scan."""
    session = get_sync_session()
    temp_dir: Path | None = None
    scan_uuid = uuid.UUID(scan_id)

    try:
        scan = session.execute(select(Scan).where(Scan.id == scan_uuid)).scalar_one_or_none()
        if scan is None:
            logger.error("Scan not found", scan_id=scan_id)
            return

        bind_pipeline_context(
            scan_id=scan_id,
            doctor_id=str(scan.doctor_id) if scan.doctor_id else None,
            detector_model=scan.detector_model,
        )
        logger.info("Scan processing started")

        _update_scan(
            session,
            scan,
            status=ScanStatus.processing,
            started_at=datetime.now(UTC),
            progress_message="Loading scan data...",
        )

        temp_dir = Path(tempfile.mkdtemp(prefix=f"scan_{scan_id}_"))
        prefix = scan.raw_frames_prefix or storage_service.scan_frames_prefix(scan_id)
        frame_paths = _download_frames(prefix, temp_dir)
        _update_scan(session, scan, progress_message="Frames downloaded. Initialising detector...")

        detector = _get_detector()
        _update_scan(session, scan, progress_message="Running keypoint detection...")
        raw_keypoints = detector.detect(frame_paths)
        frame_landmarks = list(raw_keypoints.get("landmarks", []))

        keypoints = KeypointNormalizer.normalize(raw_keypoints, scan.detector_model)
        _update_scan(session, scan, progress_message="Keypoints normalised. Running 3D reconstruction...")

        calibration = CalibrationData(
            patient_height_cm=scan.patient_height_cm,
            patient_weight_kg=scan.patient_weight_kg,
            camera_height_cm=scan.camera_height_cm,
            camera_distance_cm=scan.camera_distance_cm,
        )
        keypoints_3d = Reconstructor3D.reconstruct(keypoints, None, calibration)
        _update_scan(session, scan, progress_message="Fitting spine curve model...")
        spine_curve = SpineCurveModel.fit(keypoints_3d)

        _update_scan(session, scan, progress_message="Computing posture metrics...")
        metrics = compute_all(keypoints_3d, spine_curve, calibration, None)
        overall_risk = derive_overall_risk(metrics)

        twin_key = f"scans/{scan_id}/twin/keypoints.json"
        storage_service.upload_bytes(
            twin_key,
            json.dumps(_keypoints_to_json(keypoints_3d)).encode("utf-8"),
            "application/json",
        )

        patient = session.execute(select(Patient).where(Patient.id == scan.patient_id)).scalar_one()
        _worsen_patient_risk(patient, overall_risk)

        scan.status = ScanStatus.completed
        scan.completed_at = datetime.now(UTC)
        scan.progress_message = "Analysis complete."
        scan.keypoints_json = {
            "landmarks": _keypoints_to_json(keypoints_3d),
            "frame_landmarks": frame_landmarks,
        }
        scan.metrics_json = metrics
        scan.overall_risk = RiskLevel(overall_risk)
        scan.digital_twin_url = twin_key
        session.commit()
        logger.info("Scan processing completed", overall_risk=overall_risk)
    except Exception as exc:
        session.rollback()
        scan = session.execute(select(Scan).where(Scan.id == scan_uuid)).scalar_one_or_none()
        if scan is not None:
            scan.status = ScanStatus.failed
            scan.error_message = str(exc)
            scan.progress_message = "Processing failed."
            session.commit()
        logger.exception("Scan processing failed", error=str(exc))
        raise self.retry(exc=exc)
    finally:
        clear_pipeline_context()
        session.close()
        if temp_dir and temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
