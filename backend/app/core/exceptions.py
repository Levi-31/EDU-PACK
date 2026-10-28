class PlaylistScholarException(Exception):
    """Base exception for Playlist Scholar"""
    def __init__(self, message: str, status_code: int = 500, details: dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class InvalidPlaylistException(PlaylistScholarException):
    def __init__(self, message: str = "Invalid YouTube playlist ID or URL", details: dict = None):
        super().__init__(message, status_code=400, details=details)


class PlaylistNotFoundException(PlaylistScholarException):
    def __init__(self, message: str = "YouTube playlist not found or private", details: dict = None):
        super().__init__(message, status_code=404, details=details)


class TranscriptUnavailableException(PlaylistScholarException):
    def __init__(self, message: str = "Transcript not available for this video", details: dict = None):
        super().__init__(message, status_code=404, details=details)


class JobNotFoundException(PlaylistScholarException):
    def __init__(self, job_id: str):
        super().__init__(f"Job with ID {job_id} not found", status_code=404, details={"job_id": job_id})


class LLMGenerationException(PlaylistScholarException):
    def __init__(self, message: str = "Failed to generate LLM response", details: dict = None):
        super().__init__(message, status_code=502, details=details)


class PDFGenerationException(PlaylistScholarException):
    def __init__(self, message: str = "Failed to compile PDF artifact", details: dict = None):
        super().__init__(message, status_code=500, details=details)


class StorageException(PlaylistScholarException):
    def __init__(self, message: str = "Storage operation failed", details: dict = None):
        super().__init__(message, status_code=500, details=details)
