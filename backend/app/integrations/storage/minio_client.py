import io
import json
import logging
import mimetypes
from pathlib import Path
from typing import Optional, Union

import urllib3
from minio import Minio
from minio.error import S3Error
from app.core.config import settings

logger = logging.getLogger(__name__)


class MinIOStorageService:
    """
    Singleton service managing S3-compatible object storage via MinIO.
    Stores and serves generated images, PDFs, markdown, and archive bundles.
    """
    _instance: Optional["MinIOStorageService"] = None

    def __init__(self):
        self.endpoint = settings.MINIO_ENDPOINT
        self.access_key = settings.MINIO_ROOT_USER
        self.secret_key = settings.MINIO_ROOT_PASSWORD
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self.public_url = settings.MINIO_PUBLIC_URL.rstrip("/")
        self.secure = settings.MINIO_SECURE

        self._client: Optional[Minio] = None
        self._available: bool = False
        self._init_client()

    @classmethod
    def get_instance(cls) -> "MinIOStorageService":
        if cls._instance is None:
            cls._instance = MinIOStorageService()
        return cls._instance

    def _create_http_client(self) -> urllib3.PoolManager:
        return urllib3.PoolManager(
            timeout=urllib3.Timeout(connect=2.0, read=10.0),
            retries=urllib3.Retry(total=1, backoff_factor=0.2)
        )

    def _init_client(self):
        endpoints_to_try = [self.endpoint]
        if "minio:" in self.endpoint:
            endpoints_to_try.append(self.endpoint.replace("minio:", "localhost:"))

        for ep in endpoints_to_try:
            try:
                client = Minio(
                    ep,
                    access_key=self.access_key,
                    secret_key=self.secret_key,
                    secure=self.secure,
                    http_client=self._create_http_client()
                )
                client.list_buckets()
                self._client = client
                self.endpoint = ep
                self._available = True
                logger.info(f"Connected to MinIO at {ep}")
                self._ensure_bucket()
                return
            except Exception as e:
                logger.debug(f"Could not connect to MinIO at {ep}: {e}")

        self._available = False
        try:
            self._client = Minio(
                self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.secure,
                http_client=self._create_http_client()
            )
        except Exception as ex:
            logger.warning(f"MinIO client instantiation note: {ex}")

    def _ensure_bucket(self):
        if not self._client or not self._available:
            return
        try:
            if not self._client.bucket_exists(self.bucket_name):
                self._client.make_bucket(self.bucket_name)
                logger.info(f"Created MinIO bucket '{self.bucket_name}'")

            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "PublicReadGetObject",
                        "Effect": "Allow",
                        "Principal": {"AWS": ["*"]},
                        "Action": ["s3:GetObject"],
                        "Resource": [f"arn:aws:s3:::{self.bucket_name}/*"]
                    }
                ]
            }
            self._client.set_bucket_policy(self.bucket_name, json.dumps(policy))
        except Exception as e:
            logger.warning(f"MinIO bucket check/policy setup note: {e}")

    def is_available(self) -> bool:
        return self._available and self._client is not None

    def get_public_url(self, object_name: str) -> str:
        clean_obj = object_name.lstrip("/")
        return f"{self.public_url}/{self.bucket_name}/{clean_obj}"

    def upload_file(
        self,
        local_path: Union[str, Path],
        object_name: str,
        content_type: Optional[str] = None
    ) -> str:
        p = Path(local_path)
        if not p.exists():
            raise FileNotFoundError(f"File not found: {local_path}")

        clean_obj = object_name.lstrip("/")
        if not self._available or not self._client:
            return self.get_public_url(clean_obj)

        if not content_type:
            mime, _ = mimetypes.guess_type(str(p))
            content_type = mime or "application/octet-stream"

        try:
            self._client.fput_object(
                bucket_name=self.bucket_name,
                object_name=clean_obj,
                file_path=str(p),
                content_type=content_type
            )
            return self.get_public_url(clean_obj)
        except Exception as e:
            logger.warning(f"Failed to upload {clean_obj} to MinIO: {e}")
            self._available = False
            return self.get_public_url(clean_obj)

    def upload_bytes(
        self,
        data: bytes,
        object_name: str,
        content_type: str = "application/octet-stream"
    ) -> str:
        clean_obj = object_name.lstrip("/")
        if not self._available or not self._client:
            return self.get_public_url(clean_obj)

        try:
            stream = io.BytesIO(data)
            self._client.put_object(
                bucket_name=self.bucket_name,
                object_name=clean_obj,
                data=stream,
                length=len(data),
                content_type=content_type
            )
            return self.get_public_url(clean_obj)
        except Exception as e:
            logger.warning(f"Failed to upload bytes {clean_obj} to MinIO: {e}")
            self._available = False
            return self.get_public_url(clean_obj)


storage_service = MinIOStorageService.get_instance()
