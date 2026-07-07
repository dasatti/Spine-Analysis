"""Dataset item CRUD and keypoint inference for research data generation."""

from __future__ import annotations

import asyncio
import copy
import math
import os
import tempfile
import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.manual_labels import MANUAL_LABEL_KEYS
from app.models.dataset_item import DatasetItem, DatasetItemStatus, DatasetPoseType
from app.models.doctor import Doctor
from app.pipeline.landmark_mapping import twin_landmarks_from_frame
from app.pipeline.landmark_refresh import refresh_frame_landmarks
from app.pipeline.pose_inference import detect_landmarks_in_frame as spinepose_detect
from app.pipeline.yolo_inference import detect_landmarks_in_frame as yolo_detect
from app.schemas.dataset import (
    DatasetItemCreateResponse,
    DatasetItemDetailResponse,
    DatasetItemListItem,
    DatasetItemListResponse,
    DatasetManualLabelsRequest,
    DatasetRecomputeRequest,
)
from app.services.storage_service import resolve_frame_format, storage_service
from app.utils.exceptions import bad_request, not_found

SUPPORTED_DETECTORS = {"spinepose_v2", "yolo_v8"}


def _normalize_detector(model: str) -> str:
    normalized = model.strip().lower()
    aliases = {
        "spinepose": "spinepose_v2",
        "yolo": "yolo_v8",
    }
    resolved = aliases.get(normalized, normalized)
    if resolved not in SUPPORTED_DETECTORS:
        raise bad_request(f"Unsupported detector model: {model}")
    return resolved


def _run_inference(image_path: str, pose_type: str, detector_model: str) -> list[dict]:
    if detector_model == "spinepose_v2":
        return spinepose_detect(image_path, pose_type)
    return yolo_detect(image_path, pose_type, variant=detector_model)


def _keypoint_count(keypoints_json: dict | None) -> int:
    if not keypoints_json:
        return 0
    frames = keypoints_json.get("frame_landmarks") or []
    return len(frames)


def _item_to_list_item(item: DatasetItem) -> DatasetItemListItem:
    audit = (item.keypoints_json or {}).get("audit") or {}
    return DatasetItemListItem(
        id=item.id,
        pose_type=item.pose_type,
        detector_model=item.detector_model,
        status=item.status,
        original_filename=item.original_filename,
        image_url=storage_service.presigned_url(item.image_key) if item.image_key else None,
        keypoint_count=_keypoint_count(item.keypoints_json),
        keypoints_adjusted=bool(audit.get("adjusted_at")),
        created_at=item.created_at,
    )


def _item_to_detail(item: DatasetItem) -> DatasetItemDetailResponse:
    audit = (item.keypoints_json or {}).get("audit") or {}
    return DatasetItemDetailResponse(
        id=item.id,
        pose_type=item.pose_type,
        detector_model=item.detector_model,
        status=item.status,
        original_filename=item.original_filename,
        image_url=storage_service.presigned_url(item.image_key) if item.image_key else None,
        keypoints=item.keypoints_json,
        keypoints_adjusted=bool(audit.get("adjusted_at")),
        inference_error=item.inference_error,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


async def _get_item(db: AsyncSession, item_id: uuid.UUID) -> DatasetItem:
    result = await db.execute(select(DatasetItem).where(DatasetItem.id == item_id))
    item = result.scalar_one_or_none()
    if item is None:
        raise not_found("Dataset item not found")
    return item


async def list_dataset_items(
    db: AsyncSession,
    page: int,
    page_size: int,
    pose_type: DatasetPoseType | None,
    detector_model: str | None,
    status: DatasetItemStatus | None,
) -> DatasetItemListResponse:
    query = select(DatasetItem)
    count_query = select(func.count()).select_from(DatasetItem)

    if pose_type is not None:
        query = query.where(DatasetItem.pose_type == pose_type)
        count_query = count_query.where(DatasetItem.pose_type == pose_type)
    if detector_model:
        resolved = _normalize_detector(detector_model)
        query = query.where(DatasetItem.detector_model == resolved)
        count_query = count_query.where(DatasetItem.detector_model == resolved)
    if status is not None:
        query = query.where(DatasetItem.status == status)
        count_query = count_query.where(DatasetItem.status == status)

    total = (await db.execute(count_query)).scalar_one()
    total_pages = max(1, math.ceil(total / page_size)) if total else 1
    result = await db.execute(
        query.order_by(DatasetItem.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = [_item_to_list_item(item) for item in result.scalars().all()]
    return DatasetItemListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


async def get_dataset_item(db: AsyncSession, item_id: uuid.UUID) -> DatasetItemDetailResponse:
    item = await _get_item(db, item_id)
    return _item_to_detail(item)


def _process_inference_sync(item_id: uuid.UUID, image_key: str, pose_type: str, detector_model: str) -> tuple[dict | None, str | None]:
    tmp_path = None
    try:
        image_bytes = storage_service.download_bytes(image_key)
        ext = image_key.rsplit(".", 1)[-1]
        with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name
        landmarks = _run_inference(tmp_path, pose_type, detector_model)
        twin_landmarks = twin_landmarks_from_frame(landmarks)
        keypoints_json = {
            "frame_landmarks": landmarks,
            "twin_landmarks": twin_landmarks,
            "audit": {
                "original_frame_landmarks": copy.deepcopy(landmarks),
                "original_twin_landmarks": copy.deepcopy(twin_landmarks),
                "history": [],
            },
        }
        return keypoints_json, None
    except Exception as exc:
        return None, str(exc)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


async def _process_item_inference(db: AsyncSession, item: DatasetItem) -> None:
    item.status = DatasetItemStatus.processing
    await db.commit()
    keypoints_json, error = await asyncio.to_thread(
        _process_inference_sync,
        item.id,
        item.image_key,
        item.pose_type.value,
        item.detector_model,
    )
    item = await _get_item(db, item.id)
    if error:
        item.status = DatasetItemStatus.failed
        item.inference_error = error
    else:
        item.status = DatasetItemStatus.ready
        item.keypoints_json = keypoints_json
        item.inference_error = None
    await db.commit()
    await db.refresh(item)


async def create_dataset_items(
    db: AsyncSession,
    admin: Doctor,
    uploads: list[tuple[bytes, str | None, str | None]],
    pose_type: DatasetPoseType,
    detector_model: str,
) -> DatasetItemCreateResponse:
    resolved_model = _normalize_detector(detector_model)
    created_items: list[DatasetItem] = []

    for data, content_type, filename in uploads:
        item_id = uuid.uuid4()
        ext, resolved_ct = resolve_frame_format(content_type, filename)
        image_key = storage_service.dataset_image_key(str(item_id), pose_type.value, ext)
        storage_service.upload_bytes(image_key, data, resolved_ct)

        item = DatasetItem(
            id=item_id,
            created_by_doctor_id=admin.id,
            pose_type=pose_type,
            detector_model=resolved_model,
            status=DatasetItemStatus.pending,
            original_filename=filename,
            image_key=image_key,
            image_content_type=resolved_ct,
        )
        db.add(item)
        created_items.append(item)

    await db.commit()
    for item in created_items:
        await db.refresh(item)
        await _process_item_inference(db, item)
        await db.refresh(item)

    details = [_item_to_detail(item) for item in created_items]
    return DatasetItemCreateResponse(items=details, created_count=len(details))


def _recompute_keypoints(
    item: DatasetItem,
    frame_landmarks: list[dict],
    *,
    doctor_id: uuid.UUID | None,
    preserve_manual_spine: bool = False,
    refresh_synthetics: bool = False,
    note: str | None = None,
) -> dict:
    prior = copy.deepcopy(item.keypoints_json or {})
    audit = copy.deepcopy(prior.get("audit") or {})
    audit.setdefault("history", [])

    if not audit.get("original_frame_landmarks"):
        audit["original_frame_landmarks"] = copy.deepcopy(
            prior.get("frame_landmarks") or frame_landmarks
        )
        audit["original_twin_landmarks"] = copy.deepcopy(prior.get("twin_landmarks") or [])

    working = copy.deepcopy(frame_landmarks)
    if refresh_synthetics:
        working = refresh_frame_landmarks(
            working,
            preserve_manual_spine=preserve_manual_spine,
        )

    twin_landmarks = twin_landmarks_from_frame(working)
    audit["adjusted_at"] = datetime.now(UTC).isoformat()
    if doctor_id:
        audit["adjusted_by"] = str(doctor_id)
    audit["preserve_manual_spine"] = preserve_manual_spine
    audit["twin_rebuilt"] = True
    audit["history"] = list(audit.get("history") or [])[-19:] + [
        {
            "at": audit["adjusted_at"],
            "by": audit.get("adjusted_by"),
            "action": "manual_recompute",
            "note": note,
        }
    ]

    return {
        "frame_landmarks": working,
        "twin_landmarks": twin_landmarks,
        "audit": audit,
    }


def _preserve_manual_labels(existing: dict | None, updated: dict) -> dict:
    if isinstance(existing, dict) and existing.get("manual_labels"):
        updated["manual_labels"] = copy.deepcopy(existing["manual_labels"])
    return updated


async def save_manual_labels(
    db: AsyncSession,
    admin: Doctor,
    item_id: uuid.UUID,
    payload: DatasetManualLabelsRequest,
) -> DatasetItemDetailResponse:
    item = await _get_item(db, item_id)
    if item.status != DatasetItemStatus.ready:
        raise bad_request("Dataset item is not ready for manual labeling")

    keypoints = copy.deepcopy(item.keypoints_json or {})
    values = payload.model_dump()
    new_labels = {
        key: value for key, value in values.items() if key in MANUAL_LABEL_KEYS and value is not None
    }

    if new_labels:
        new_labels["labeled_at"] = datetime.now(UTC).isoformat()
        new_labels["labeled_by"] = str(admin.id)
        keypoints["manual_labels"] = new_labels
    else:
        keypoints.pop("manual_labels", None)

    item.keypoints_json = keypoints
    await db.commit()
    await db.refresh(item)
    return _item_to_detail(item)


async def recompute_dataset_item(
    db: AsyncSession,
    admin: Doctor,
    item_id: uuid.UUID,
    payload: DatasetRecomputeRequest,
) -> DatasetItemDetailResponse:
    item = await _get_item(db, item_id)
    if item.status != DatasetItemStatus.ready:
        raise bad_request("Dataset item is not ready for keypoint adjustment")

    frame_landmarks = [lm.model_dump(exclude_unset=True) for lm in payload.frame_landmarks]
    for lm in frame_landmarks:
        if not lm.get("view"):
            lm["view"] = item.pose_type.value

    item.keypoints_json = _preserve_manual_labels(
        item.keypoints_json,
        _recompute_keypoints(
            item,
            frame_landmarks,
            doctor_id=admin.id,
            preserve_manual_spine=payload.preserve_manual_spine,
            refresh_synthetics=payload.refresh_synthetics,
            note=payload.note,
        ),
    )
    await db.commit()
    await db.refresh(item)
    return _item_to_detail(item)


async def reset_dataset_item_keypoints(
    db: AsyncSession,
    admin: Doctor,
    item_id: uuid.UUID,
    note: str | None = None,
) -> DatasetItemDetailResponse:
    item = await _get_item(db, item_id)
    audit = (item.keypoints_json or {}).get("audit") or {}
    original = audit.get("original_frame_landmarks")
    if not original:
        raise bad_request("No original keypoints stored for this item")

    original_twin = audit.get("original_twin_landmarks") or twin_landmarks_from_frame(original)
    new_audit = {
        "original_frame_landmarks": copy.deepcopy(original),
        "original_twin_landmarks": copy.deepcopy(original_twin),
        "history": list(audit.get("history") or []) + [
            {
                "at": datetime.now(UTC).isoformat(),
                "by": str(admin.id),
                "action": "reset_keypoints",
                "note": note,
            }
        ],
    }
    item.keypoints_json = _preserve_manual_labels(
        item.keypoints_json,
        {
            "frame_landmarks": copy.deepcopy(original),
            "twin_landmarks": copy.deepcopy(original_twin),
            "audit": new_audit,
        },
    )
    await db.commit()
    await db.refresh(item)
    return _item_to_detail(item)
