import json
import os

from deadlock_assets_api.models.v2.generic_data import GenericDataV2


def closest_version_file(
    client_version: int, filename: str, versions_folder: str = "deploy/versions"
) -> str:
    exact_path = f"{versions_folder}/{client_version}/{filename}"
    if os.path.exists(exact_path):
        return exact_path

    candidates = []
    if os.path.isdir(versions_folder):
        for version in os.listdir(versions_folder):
            if not version.isdigit():
                continue
            filepath = f"{versions_folder}/{version}/{filename}"
            if os.path.exists(filepath):
                candidates.append(int(version))

    if not candidates:
        return exact_path

    closest_version = min(candidates, key=lambda version: (abs(version - client_version), -version))
    return f"{versions_folder}/{closest_version}/{filename}"


def backfill_historical_version_files(
    out_folder: str, client_versions: list[int], default_images_data: dict
) -> None:
    available_image_versions: list[int] = []

    for version_id in client_versions:
        version_folder = f"{out_folder}/versions/{version_id}"
        os.makedirs(version_folder, exist_ok=True)

        generic_source = f"res/builds/{version_id}/v2/generic_data.json"
        generic_target = f"{version_folder}/generic_data.json"
        if os.path.exists(generic_source) and not os.path.exists(generic_target):
            with open(generic_source) as f:
                generic_data = GenericDataV2.model_validate_json(f.read())
            with open(generic_target, "w") as f:
                f.write(generic_data.model_dump_json(exclude_none=True))

        if os.path.exists(f"{version_folder}/images_data.json"):
            available_image_versions.append(version_id)

    for version_id in client_versions:
        version_folder = f"{out_folder}/versions/{version_id}"
        images_target = f"{version_folder}/images_data.json"
        if os.path.exists(images_target):
            continue

        closest_version = min(
            available_image_versions,
            key=lambda candidate: (abs(candidate - version_id), -candidate),
            default=None,
        )
        if closest_version is not None:
            with open(f"{out_folder}/versions/{closest_version}/images_data.json") as f:
                images_data = json.load(f)
        else:
            images_data = default_images_data

        with open(images_target, "w") as f:
            json.dump(images_data, f)
