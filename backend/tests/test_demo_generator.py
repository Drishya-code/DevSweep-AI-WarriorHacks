from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from generate_demo import generate_demo


def test_compact_demo_reset_is_repeatable_and_preserves_project_files(tmp_path):
    demo_root = tmp_path / "demo-project"
    source = demo_root / "src" / "main.tsx"
    manifest = demo_root / "package.json"
    env_file = demo_root / ".env"
    source.parent.mkdir(parents=True)
    source.write_text("export const safe = true;", encoding="utf-8")
    manifest.write_text('{"name":"synthetic-demo"}', encoding="utf-8")
    env_file.write_text("DEMO_VALUE=placeholder-only\n", encoding="utf-8")

    generate_demo(demo_root=demo_root, compact=True)
    first_build = (demo_root / "dist" / "bundle.0.js").read_bytes()
    first_temp = (demo_root / "temp-artifact.tmp").read_bytes()
    first_uncertain_size = (demo_root / "review-me" / "unclassified.bin").stat().st_size

    (demo_root / "dist" / "stale-file.tmp").write_text("old run", encoding="utf-8")
    generate_demo(demo_root=demo_root, compact=True)

    assert (demo_root / "dist" / "bundle.0.js").read_bytes() == first_build
    assert (demo_root / "temp-artifact.tmp").read_bytes() == first_temp
    assert (demo_root / "review-me" / "unclassified.bin").stat().st_size == first_uncertain_size
    assert not (demo_root / "dist" / "stale-file.tmp").exists()
    assert source.read_text(encoding="utf-8") == "export const safe = true;"
    assert manifest.read_text(encoding="utf-8") == '{"name":"synthetic-demo"}'
    assert env_file.read_text(encoding="utf-8") == "DEMO_VALUE=placeholder-only\n"
