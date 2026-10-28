from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Tuple


class StorageProvider(ABC):
    @abstractmethod
    def save_bytes(self, relative_path: str, data: bytes, mime_type: str = "application/octet-stream") -> Tuple[str, int, str]:
        """Saves bytes and returns (absolute_file_path, file_size_bytes, sha256_checksum)"""
        pass

    @abstractmethod
    def get_file_path(self, relative_path: str) -> Optional[Path]:
        """Returns the local path if available, or None"""
        pass

    @abstractmethod
    def read_bytes(self, relative_path: str) -> Optional[bytes]:
        """Reads file bytes"""
        pass

    @abstractmethod
    def exists(self, relative_path: str) -> bool:
        """Checks if file exists"""
        pass

    @abstractmethod
    def delete(self, relative_path: str) -> bool:
        """Deletes file"""
        pass
