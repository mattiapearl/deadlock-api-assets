import importlib
import json
import sys
import types
from pathlib import Path

import pytest
from fastapi import HTTPException
from pydantic import TypeAdapter

from deadlock_assets_api.models.v2.generic_data import GenericDataV2


REPO_ROOT = Path(__file__).resolve().parents[1]


def prepare_runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    deploy = tmp_path / "deploy"
    deploy.mkdir()
    (deploy / "client_versions.json").write_text(json.dumps([6016, 5959]))

    css_parser = types.ModuleType("css_parser")
    css_parser.parseFile = lambda *_args, **_kwargs: types.SimpleNamespace(cssRules=[])
    css_parser.parseString = lambda *_args, **_kwargs: types.SimpleNamespace(cssRules=[])
    css_module = types.ModuleType("css_parser.css")
    css_module.CSSRuleList = list
    css_module.CSSStyleRule = type("CSSStyleRule", (), {})
    css_module.ColorValue = type("ColorValue", (), {})
    css_module.CSSUnknownRule = type("CSSUnknownRule", (), {})
    monkeypatch.setitem(sys.modules, "css_parser", css_parser)
    monkeypatch.setitem(sys.modules, "css_parser.css", css_module)
    stringcase = types.ModuleType("stringcase")
    stringcase.snakecase = lambda value: value
    monkeypatch.setitem(sys.modules, "stringcase", stringcase)

    for module_name in [
        "deadlock_assets_api.models.enums",
        "deadlock_assets_api.utils",
    ]:
        sys.modules.pop(module_name, None)


def test_generic_data_model_accepts_old_minimal_snapshots() -> None:
    payload = json.loads((REPO_ROOT / "res/builds/5959/v2/generic_data.json").read_text())

    generic_data = GenericDataV2.model_validate(payload)

    assert generic_data.item_price_per_tier == [0, 800, 1600, 3200, 6400, 9999]
    assert generic_data.lane_info is None
    assert generic_data.weapon_groups is None


def test_generic_data_model_accepts_legacy_street_brawl_draft_shape() -> None:
    payload = json.loads((REPO_ROOT / "res/builds/6351/v2/generic_data.json").read_text())

    generic_data = GenericDataV2.model_validate(payload)

    first_round = generic_data.street_brawl.item_draft_rounds_per_game_round[0].item_draft_rounds[0]
    assert first_round.normal_mod_tier.value == 2
    assert first_round.rare_mod_tier.value == 1
    assert generic_data.street_brawl.item_drafts is None


def test_missing_generated_file_returns_404_instead_of_500(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    prepare_runtime(tmp_path, monkeypatch)
    utils = importlib.import_module("deadlock_assets_api.utils")

    with pytest.raises(HTTPException) as exc_info:
        utils.read_parse_data_ta(
            "deploy/versions/5959/images_data.json", TypeAdapter(dict[str, str])
        )

    assert exc_info.value.status_code == 404


def test_backfills_historical_generic_data(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    prepare_runtime(tmp_path, monkeypatch)
    source_folder = tmp_path / "res/builds/5959/v2"
    source_folder.mkdir(parents=True)
    source_folder.joinpath("generic_data.json").write_text(
        (REPO_ROOT / "res/builds/5959/v2/generic_data.json").read_text()
    )

    historical = importlib.import_module("deadlock_assets_api.historical")

    historical.backfill_historical_generic_data("deploy", [6016, 5959])

    generic_data = json.loads((tmp_path / "deploy/versions/5959/generic_data.json").read_text())
    assert generic_data["item_price_per_tier"] == [0, 800, 1600, 3200, 6400, 9999]
    assert "lane_info" not in generic_data
