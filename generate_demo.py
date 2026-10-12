#!/usr/bin/env python3
"""
Generate realistic demo project with actual files of real sizes.
This script is run locally to create demo data - NOT committed to git.
"""

import random
import shutil
from pathlib import Path

DEMO_ROOT = Path(__file__).parent / "demo-project"


def write_fixture_file(path: Path, size: int, label: str) -> None:
    """Write harmless, repeatable fixture bytes without depending on OS randomness."""
    path.parent.mkdir(parents=True, exist_ok=True)
    seed = (label.encode("utf-8") + b" | DevSweep synthetic demo | ")
    block = (seed * ((4096 // len(seed)) + 1))[:4096]
    remaining = size
    with path.open("wb") as output:
        while remaining:
            chunk = block[:min(len(block), remaining)]
            output.write(chunk)
            remaining -= len(chunk)

def generate_demo(demo_root: Path = DEMO_ROOT, compact: bool = False):
    """Generate realistic demo project with actual file sizes."""
    rng = random.Random(42)
    package_count = 5 if compact else 500
    dist_count = 3 if compact else 50
    vite_count = 4 if compact else 100
    log_count = 2 if compact else 50
    cache_count = 2 if compact else 50
    coverage_count = 2 if compact else 30
    nyc_count = 2 if compact else 20
    # Clean existing demo dirs
    dirs_to_clean = ["node_modules", "dist", ".vite", "logs", "cache", "coverage", ".nyc_output", "review-me"]
    for d in dirs_to_clean:
        path = demo_root / d
        if path.exists():
            shutil.rmtree(path)
    
    # Create directories
    for d in dirs_to_clean:
        (demo_root / d).mkdir(parents=True, exist_ok=True)
    
    # 1. node_modules - simulate with many small files (typical npm install)
    print("Generating node_modules...")
    node_modules = demo_root / "node_modules"
    for i in range(package_count):
        pkg_dir = node_modules / f"pkg-{i}"
        pkg_dir.mkdir()
        # Each package has a few files
        for j in range(rng.randint(2, 10)):
            file_path = pkg_dir / f"file{j}.js"
            size = rng.randint(1000, 50000)  # 1KB - 50KB per file
            write_fixture_file(file_path, size, f"package-{i}-{j}")
    
    # 2. dist - build output
    print("Generating dist...")
    dist = demo_root / "dist"
    for i in range(dist_count):
        file_path = dist / f"bundle.{i}.js"
        size = rng.randint(10000, 500000)  # 10KB - 500KB
        write_fixture_file(file_path, size, f"bundle-{i}")
    # Add some .map and .css files
    for i in range(2 if compact else 10):
        file_path = dist / f"style.{i}.css"
        size = rng.randint(5000, 100000)
        write_fixture_file(file_path, size, f"style-{i}")
        file_path = dist / f"bundle.{i}.js.map"
        size = rng.randint(50000, 300000)
        write_fixture_file(file_path, size, f"bundle-map-{i}")
    
    # 3. .vite - cache
    print("Generating .vite...")
    vite = demo_root / ".vite"
    for i in range(vite_count):
        file_path = vite / f"cache.{i}.data"
        size = rng.randint(1000, 20000)
        write_fixture_file(file_path, size, f"vite-cache-{i}")
    
    # 4. logs - log files (larger to trigger CAUTION > 10MB)
    print("Generating logs...")
    logs = demo_root / "logs"
    for i in range(log_count):
        file_path = logs / f"app-{i}.log"
        size = rng.randint(200000, 500000)  # 200KB - 500KB
        write_fixture_file(file_path, size, f"log-{i}")
    
    # 5. cache - general cache (larger to trigger CAUTION > 10MB)
    print("Generating cache...")
    cache = demo_root / "cache"
    for i in range(cache_count):
        file_path = cache / f"cache-{i}.bin"
        size = rng.randint(200000, 500000)  # 200KB - 500KB
        write_fixture_file(file_path, size, f"cache-{i}")
    
    # 6. coverage - test coverage reports
    print("Generating coverage...")
    coverage = demo_root / "coverage"
    for i in range(coverage_count):
        file_path = coverage / f"coverage-{i}.json"
        size = rng.randint(10000, 200000)
        write_fixture_file(file_path, size, f"coverage-{i}")
    
    # 7. .nyc_output - nyc intermediate files
    print("Generating .nyc_output...")
    nyc = demo_root / ".nyc_output"
    for i in range(nyc_count):
        file_path = nyc / f"out-{i}.json"
        size = rng.randint(5000, 100000)
        write_fixture_file(file_path, size, f"nyc-{i}")

    # Small deterministic finding plus a deliberately uncertain >10 MiB directory.
    write_fixture_file(demo_root / "temp-artifact.tmp", 96 * 1024, "temporary compiler output")
    review_file = demo_root / "review-me" / "unclassified.bin"
    write_fixture_file(review_file, 10 * 1024 * 1024 + 128 * 1024, "uncertain user data; inspect before cleanup")
    
    print("\nDemo generation complete!")
    
    # Report actual sizes
    print("\nActual sizes:")
    for d in dirs_to_clean:
        path = demo_root / d
        total = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
        print(f"  {d}: {total / (1024*1024):.2f} MB ({total:,} bytes)")
    
    total_all = sum(
        sum(f.stat().st_size for f in (demo_root / d).rglob("*") if f.is_file())
        for d in dirs_to_clean
    )
    total_all += (demo_root / "temp-artifact.tmp").stat().st_size
    print(f"\nTotal recoverable: {total_all / (1024*1024):.2f} MB ({total_all:,} bytes)")

if __name__ == "__main__":
    generate_demo()
