import os

from deadlock_assets_api.models.v2.generic_data import GenericDataV2


def backfill_historical_generic_data(out_folder: str, client_versions: list[int]) -> None:
    for version_id in client_versions:
        version_folder = f"{out_folder}/versions/{version_id}"
        os.makedirs(version_folder, exist_ok=True)

        generic_source = f"res/builds/{version_id}/v2/generic_data.json"
        generic_target = f"{version_folder}/generic_data.json"
        if not os.path.exists(generic_source) or os.path.exists(generic_target):
            continue

        with open(generic_source) as f:
            generic_data = GenericDataV2.model_validate_json(f.read())
        with open(generic_target, "w") as f:
            f.write(generic_data.model_dump_json(exclude_none=True))
