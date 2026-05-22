import json
from pathlib import Path

from deadlock_assets_api.availability import get_client_version_availability


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload))


def test_client_version_availability_reports_payload_coverage(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    write_json(Path("deploy/versions/6016/items/english.json"), [])
    write_json(Path("deploy/versions/6016/generic_data.json"), {})
    write_json(Path("deploy/versions/6016/images_data.json"), {"image": "url"})
    write_json(Path("deploy/versions/5959/items/english.json"), [])
    write_json(Path("deploy/versions/5959/generic_data.json"), {})

    availability = get_client_version_availability([6016, 5959])

    assert availability == [
        {
            "client_version": 6016,
            "items": True,
            "generic_data": True,
            "images": True,
            "nearest_images_version": 6016,
        },
        {
            "client_version": 5959,
            "items": True,
            "generic_data": True,
            "images": False,
            "nearest_images_version": 6016,
        },
    ]


def test_client_version_availability_handles_no_image_manifests(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    write_json(Path("deploy/versions/5959/items/english.json"), [])

    availability = get_client_version_availability([5959])

    assert availability[0]["nearest_images_version"] is None
