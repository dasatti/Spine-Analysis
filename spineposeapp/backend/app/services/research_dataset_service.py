"""CRUD for named research datasets that group dataset items."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset_item import DatasetItem
from app.models.doctor import Doctor
from app.models.research_dataset import ResearchDataset
from app.schemas.dataset import (
    ResearchDatasetCreateRequest,
    ResearchDatasetListResponse,
    ResearchDatasetResponse,
    ResearchDatasetUpdateRequest,
)
from app.utils.exceptions import bad_request, not_found


def _dataset_to_response(dataset: ResearchDataset, item_count: int = 0) -> ResearchDatasetResponse:
    return ResearchDatasetResponse(
        id=dataset.id,
        name=dataset.name,
        item_count=item_count,
        created_at=dataset.created_at,
        updated_at=dataset.updated_at,
    )


async def _get_dataset(db: AsyncSession, dataset_id: uuid.UUID) -> ResearchDataset:
    result = await db.execute(select(ResearchDataset).where(ResearchDataset.id == dataset_id))
    dataset = result.scalar_one_or_none()
    if dataset is None:
        raise not_found("Dataset not found")
    return dataset


async def _item_count(db: AsyncSession, dataset_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.count()).select_from(DatasetItem).where(DatasetItem.dataset_id == dataset_id)
    )
    return int(result.scalar_one())


async def list_research_datasets(db: AsyncSession) -> ResearchDatasetListResponse:
    result = await db.execute(
        select(
            ResearchDataset,
            func.count(DatasetItem.id).label("item_count"),
        )
        .outerjoin(DatasetItem, DatasetItem.dataset_id == ResearchDataset.id)
        .group_by(ResearchDataset.id)
        .order_by(ResearchDataset.name.asc())
    )
    datasets = [_dataset_to_response(row[0], int(row[1] or 0)) for row in result.all()]
    return ResearchDatasetListResponse(datasets=datasets)


async def create_research_dataset(
    db: AsyncSession,
    admin: Doctor,
    payload: ResearchDatasetCreateRequest,
) -> ResearchDatasetResponse:
    name = payload.name.strip()
    if not name:
        raise bad_request("Dataset name is required")

    dataset = ResearchDataset(
        name=name,
        created_by_doctor_id=admin.id,
    )
    db.add(dataset)
    await db.commit()
    await db.refresh(dataset)
    return _dataset_to_response(dataset, 0)


async def update_research_dataset(
    db: AsyncSession,
    dataset_id: uuid.UUID,
    payload: ResearchDatasetUpdateRequest,
) -> ResearchDatasetResponse:
    dataset = await _get_dataset(db, dataset_id)
    name = payload.name.strip()
    if not name:
        raise bad_request("Dataset name is required")

    dataset.name = name
    await db.commit()
    await db.refresh(dataset)
    item_count = await _item_count(db, dataset_id)
    return _dataset_to_response(dataset, item_count)


async def delete_research_dataset(db: AsyncSession, dataset_id: uuid.UUID) -> None:
    dataset = await _get_dataset(db, dataset_id)
    await db.delete(dataset)
    await db.commit()


async def get_research_dataset(db: AsyncSession, dataset_id: uuid.UUID) -> ResearchDataset:
    return await _get_dataset(db, dataset_id)
