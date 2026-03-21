import json
from pathlib import Path

from hir.output.json import dump_json


def test_dump_json_writes_expected_content_and_sequence(tmp_path):
    out_path_1 = dump_json(
        {"message": "áéíóú", "ok": True},
        base_filename="scan",
        directory=str(tmp_path),
    )
    out_path_2 = dump_json(
        {"message": "second"},
        base_filename="scan",
        directory=str(tmp_path),
    )

    assert Path(out_path_1).name == "scan_01.json"
    assert Path(out_path_2).name == "scan_02.json"
    assert json.loads(Path(out_path_1).read_text(encoding="utf-8")) == {
        "message": "áéíóú",
        "ok": True,
    }


def test_dump_json_uses_default_filename_when_base_name_is_missing(tmp_path):
    out_path = dump_json({"status": "ok"}, directory=str(tmp_path))

    assert Path(out_path).name == "01.json"
    assert json.loads(Path(out_path).read_text(encoding="utf-8")) == {"status": "ok"}
