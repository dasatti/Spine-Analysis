import io
import logging
from pathlib import PurePosixPath

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.config import settings

logger = logging.getLogger(__name__)

FRAME_EXTENSIONS = ("png", "jpg", "jpeg", "tif", "tiff")

CONTENT_TYPE_BY_EXT: dict[str, str] = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "tif": "image/tiff",
    "tiff": "image/tiff",
}


def resolve_frame_format(content_type: str | None, filename: str | None) -> tuple[str, str]:
    """Return (file_extension, s3_content_type) for a scan frame upload."""
    if filename and "." in filename:
        ext = filename.rsplit(".", 1)[-1].lower()
        if ext == "jpeg":
            ext = "jpg"
        if ext in CONTENT_TYPE_BY_EXT:
            return ext, CONTENT_TYPE_BY_EXT[ext if ext != "jpeg" else "jpg"]

    if content_type:
        normalized = content_type.lower().split(";")[0].strip()
        if normalized in ("image/jpeg", "image/jpg"):
            return "jpg", "image/jpeg"
        if normalized == "image/png":
            return "png", "image/png"
        if normalized in ("image/tiff", "image/tif"):
            return "tiff", "image/tiff"

    return "png", "image/png"


class StorageService:
    def __init__(self) -> None:
        scheme = "https" if settings.minio_secure else "http"
        internal_endpoint = f"{scheme}://{settings.minio_endpoint}"
        self._client = boto3.client(
            "s3",
            endpoint_url=internal_endpoint,
            aws_access_key_id=settings.minio_access_key,
            aws_secret_access_key=settings.minio_secret_key,
            config=Config(signature_version="s3v4"),
            region_name="us-east-1",
        )
        public_host = settings.minio_public_endpoint or settings.minio_endpoint
        public_endpoint = f"{scheme}://{public_host}"
        self._public_client = (
            self._client
            if public_endpoint == internal_endpoint
            else boto3.client(
                "s3",
                endpoint_url=public_endpoint,
                aws_access_key_id=settings.minio_access_key,
                aws_secret_access_key=settings.minio_secret_key,
                config=Config(signature_version="s3v4"),
                region_name="us-east-1",
            )
        )
        self._bucket = settings.minio_bucket

    def ensure_bucket(self) -> None:
        try:
            self._client.head_bucket(Bucket=self._bucket)
        except ClientError:
            self._client.create_bucket(Bucket=self._bucket)
            logger.info("Created MinIO bucket: %s", self._bucket)
        self._ensure_bucket_cors()

    def _ensure_bucket_cors(self) -> None:
        origins = set(settings.cors_origins_list)
        origins.update({"http://localhost", "http://localhost:80", "http://127.0.0.1"})
        if settings.minio_public_endpoint:
            scheme = "https" if settings.minio_secure else "http"
            origins.add(f"{scheme}://{settings.minio_public_endpoint}")
        try:
            self._client.put_bucket_cors(
                Bucket=self._bucket,
                CORSConfiguration={
                    "CORSRules": [
                        {
                            "AllowedHeaders": ["*"],
                            "AllowedMethods": ["GET", "HEAD"],
                            "AllowedOrigins": sorted(origins),
                            "ExposeHeaders": ["ETag", "Content-Length", "Content-Type"],
                            "MaxAgeSeconds": 3600,
                        }
                    ]
                },
            )
        except ClientError as exc:
            logger.warning("Could not configure MinIO bucket CORS: %s", exc)

    def upload_bytes(self, key: str, data: bytes, content_type: str) -> str:
        self._client.upload_fileobj(
            io.BytesIO(data),
            self._bucket,
            key,
            ExtraArgs={"ContentType": content_type},
        )
        return key

    def presigned_url(self, key: str, expires_in: int = 3600) -> str:
        return self._public_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_in,
        )

    def delete_prefix(self, prefix: str) -> None:
        paginator = self._client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self._bucket, Prefix=prefix):
            objects = page.get("Contents", [])
            if not objects:
                continue
            delete_keys = [{"Key": obj["Key"]} for obj in objects]
            self._client.delete_objects(
                Bucket=self._bucket,
                Delete={"Objects": delete_keys},
            )

    @staticmethod
    def scan_frames_prefix(scan_id: str) -> str:
        return f"scans/{scan_id}/frames/"

    @staticmethod
    def frame_key(scan_id: str, view: str, ext: str = "png") -> str:
        return str(PurePosixPath("scans") / scan_id / "frames" / f"{view}.{ext}")

    @staticmethod
    def dataset_image_key(item_id: str, pose_type: str, ext: str = "png") -> str:
        return str(PurePosixPath("datasets") / item_id / f"{pose_type}.{ext}")

    def download_bytes(self, key: str) -> bytes:
        buffer = io.BytesIO()
        self._client.download_fileobj(self._bucket, key, buffer)
        return buffer.getvalue()

    def find_frame_key(self, prefix: str, view: str) -> str | None:
        for ext in FRAME_EXTENSIONS:
            key = f"{prefix}{view}.{ext}"
            try:
                self._client.head_object(Bucket=self._bucket, Key=key)
                return key
            except ClientError:
                continue
        return None


storage_service = StorageService()
