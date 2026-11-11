"""Storage SDK.

HTTP client for the object storage gateway. Callers mint the service ticket.
This package does not upload bytes to the bucket.
"""

from storage_sdk.client import StorageClient
from storage_sdk.errors import StorageError

__version__ = "1.0.1"

__all__ = [
    "StorageError",
    "StorageClient",
]
