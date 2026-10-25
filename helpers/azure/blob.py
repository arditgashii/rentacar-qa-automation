"""Looks inside Azure Blob Storage (Azurite locally) to prove a photo really landed there."""

from azure.storage.blob import BlobServiceClient

from config.settings import get_settings


def blob_storage_configured() -> bool:
    return bool(get_settings().azure_storage_connection_string)


def blob_properties(blob_name: str) -> dict[str, object] | None:
    """Size and content type of a blob, or None when it does not exist."""
    settings = get_settings()
    service = BlobServiceClient.from_connection_string(settings.azure_storage_connection_string)
    blob = service.get_blob_client(settings.photo_container, blob_name)
    if not blob.exists():
        return None
    properties = blob.get_blob_properties()
    return {"size": properties.size, "content_type": properties.content_settings.content_type}


def blob_name_from_url(url: str) -> str:
    """`/media/cars/7/ab12.jpg` -> `cars/7/ab12.jpg`."""
    return url.removeprefix("/media/")
