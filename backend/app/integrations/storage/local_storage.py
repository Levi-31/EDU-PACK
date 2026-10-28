import hashlib
import os
from pathlib import Path
from typing import Optional, Tuple
from app.core.config import settings
from app.core.exceptions import StorageException
from app.integrations.storage.base import StorageProvider


class LocalStorageProvider(StorageProvider):
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir or settings.STORAGE_DIR).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_safe_path(self, relative_path: str) -> Path:
        clean_rel = relative_path.lstrip("/\\")
        target_path = (self.base_dir / clean_rel).resolve()
        # Security: verify path traversal is prevented
        if not str(target_path).startswith(str(self.base_dir)):
            raise StorageException(f"Illegal path traversal detected: {relative_path}")
        return target_path

    def save_bytes(self, relative_path: str, data: bytes, mime_type: str = "application/octet-stream") -> Tuple[str, int, str]:
        target_path = self._resolve_safe_path(relative_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        target_path.write_bytes(data)
        file_size = len(data)
        checksum = hashlib.sha256(data).hexdigest()
        return str(target_path), file_size, checksum

    def get_file_path(self, relative_path: str) -> Optional[Path]:
        target_path = self._resolve_safe_path(relative_path)
        if target_path.is_file():
            return target_path
        return None

    def read_bytes(self, relative_path: str) -> Optional[bytes]:
        target_path = self._resolve_safe_path(relative_path)
        if target_path.is_file():
            return target_path.read_bytes()
        return None

    def exists(self, relative_path: str) -> bool:
        target_path = self._resolve_safe_path(relative_path)
        return target_path.is_file()

    def delete(self, relative_path: str) -> bool:
        target_path = self._resolve_safe_path(relative_path)
        if target_path.is_file():
            target_path.unlink()
            return True
        return False

