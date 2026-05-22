import os
from typing import TypedDict


class ClientVersionAvailability(TypedDict):
    client_version: int
    items: bool
    generic_data: bool
    images: bool
    nearest_images_version: int | None


def version_file_exists(client_version: int, relative_path: str) -> bool:
    return os.path.exists(f"deploy/versions/{client_version}/{relative_path}")


def nearest_version_with_file(
    client_version: int, client_versions: list[int], relative_path: str
) -> int | None:
    candidates = [
        version
        for version in client_versions
        if version_file_exists(version, relative_path)
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda version: (abs(version - client_version), -version))


def get_client_version_availability(
    client_versions: list[int],
) -> list[ClientVersionAvailability]:
    return [
        {
            "client_version": version,
            "items": version_file_exists(version, "items/english.json"),
            "generic_data": version_file_exists(version, "generic_data.json"),
            "images": version_file_exists(version, "images_data.json"),
            "nearest_images_version": nearest_version_with_file(
                version, client_versions, "images_data.json"
            ),
        }
        for version in client_versions
    ]
