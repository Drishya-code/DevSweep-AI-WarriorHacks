from pathlib import Path
import importlib.util

import pytest

_DEMO_SCRIPT = Path(__file__).resolve().parents[2] / "generate_demo.py"
_SPEC = importlib.util.spec_from_file_location("devsweep_generate_demo_test", _DEMO_SCRIPT)
assert _SPEC and _SPEC.loader
_DEMO_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_DEMO_MODULE)
generate_demo = _DEMO_MODULE.generate_demo


def test_compact_demo_reset_rebuilds_only_its_fixture(tmp_path):
    sandbox = tmp_path / "demo-project"
    outside = tmp_path / "outside-user-data.txt"
    outside.write_text("preserve me", encoding="utf-8")
    (sandbox / "dist").mkdir(parents=True)
    (sandbox / "dist" / "stale.bin").write_text("stale", encoding="utf-8")
    generate_demo(sandbox, compact=True)

    assert (sandbox / "temp-artifact.tmp").stat().st_size == 96 * 1024
    assert not (sandbox / "dist" / "stale.bin").exists()
    assert (sandbox / "dist").is_dir()
    assert outside.read_text(encoding="utf-8") == "preserve me"


def test_demo_reset_refuses_linked_content_without_touching_target(tmp_path):
    sandbox = tmp_path / "demo-project"
    outside = tmp_path / "outside"
    sandbox.mkdir()
    outside.mkdir()
    sentinel = outside / "keep.txt"
    sentinel.write_text("untouched", encoding="utf-8")
    link = sandbox / "node_modules"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("Directory symlink creation is unavailable.")

    with pytest.raises(ValueError, match="linked demo content"):
        generate_demo(sandbox, compact=True)
    assert sentinel.read_text(encoding="utf-8") == "untouched"


def test_demo_reset_rejects_arbitrary_folder_without_modifying_it(tmp_path):
    arbitrary = tmp_path / "user-project"
    arbitrary.mkdir()
    marker = arbitrary / "important.txt"
    marker.write_text("keep", encoding="utf-8")

    with pytest.raises(ValueError, match="dedicated demo-project"):
        generate_demo(arbitrary, compact=True)
    assert marker.read_text(encoding="utf-8") == "keep"
