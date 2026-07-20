from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )

    database_url: str
    redis_url: str
    minio_endpoint: str
    minio_public_endpoint: str | None = None
    minio_access_key: str = Field(validation_alias="MINIO_ROOT_USER")
    minio_secret_key: str = Field(validation_alias="MINIO_ROOT_PASSWORD")
    minio_bucket: str = "spinepose-scans"
    minio_secure: bool = False
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440
    cors_origins: str = "http://localhost:3000"
    detector_model: str = "spinepose_v2"
    model_weights_path: str | None = None
    kyphosis_classifier_weights_path: str | None = None
    lordosis_classifier_weights_path: str | None = None
    scoliosis_detector_weights_path: str | None = None
    # Scoliosis: max lateral keypoint deviation / back height (tune via .env)
    scoliosis_lateral_index_threshold: float = 0.05
    scoliosis_keypoint_conf_threshold: float = 0.15
    scoliosis_min_keypoints: int = 3
    # Keypoint-based scoliosis screening (back + Adams pose landmarks)
    keypoint_scoliosis_scapula_threshold: float = 0.05
    keypoint_scoliosis_spine_drift_mm_threshold: float = 10.0
    keypoint_scoliosis_rotation_threshold: float = 0.03
    keypoint_scoliosis_score_threshold: float = 0.45
    keypoint_confidence_threshold: float = 0.50
    log_level: str = "INFO"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
