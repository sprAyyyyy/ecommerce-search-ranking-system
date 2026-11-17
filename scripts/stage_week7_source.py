"""Inspect and selectively stage source files from an ORIGINAL Week 7 ZIP.

Does NOT download data, run the model, publish to GitHub, or extract model/data artifacts.
The default mode only reports candidates; --apply writes approved source files.
"""
from __future__ import annotations

import argparse
import re
import stat
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
BASENAMES = {
    "Dockerfile", "docker-compose.yml", "docker-compose.yaml", "compose.yml",
    "compose.yaml", "requirements.txt", ".dockerignore", ".env.example",
    "Makefile", "pyproject.toml", "setup.cfg", "README.md",
}
SUFFIXES = {".py", ".md", ".yaml", ".yml", ".toml", ".sh", ".bat"}
REJECT_PARTS = {
    "artifacts", "data", "datasets", "models", "model", "embeddings", "checkpoints",
    "outputs", "results", "__pycache__", "site-packages", "env", ".venv",
    "notebooks", ".git", "logs", "tests_outputs",
}


def map_target(member_name: str) -> Path | None:
    """Select code/config; normalize nested ZIP roots without trusting ZIP paths."""
    if member_name.startswith("/") or "\\" in member_name or "\x00" in member_name:
        return None
    parts = PurePosixPath(member_name).parts
    if not parts or any(p in {".", ".."} for p in parts):
        return None
    if any(p.lower() in REJECT_PARTS for p in parts):
        return None
    name = parts[-1]
    if name not in BASENAMES and Path(name).suffix.lower() not in SUFFIXES:
        return None
    # Find the actual service package if nested under multiple generated directories.
    if "amazon_search_service" in parts:
        pos = parts.index("amazon_search_service")
        relative = PurePosixPath(*parts[pos:])
    else:
        # Permit top-level service launcher/config files, but not stray benchmark scripts.
        if name not in BASENAMES and not re.search(r"streamlit|app\.py$|launch|run_demo|main\.py$", name, re.I):
            return None
        relative = PurePosixPath(name)
    return ROOT / "app" / Path(*relative.parts)


def inspect_zip(path: Path, apply: bool = False) -> tuple[int, int]:
    selected, skipped = 0, 0
    seen: set[Path] = set()
    with zipfile.ZipFile(path) as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            # Reject Unix symlinks and suspiciously large source files.
            mode = (info.external_attr >> 16) & 0o170000
            if mode == stat.S_IFLNK or info.file_size > 3_000_000:
                skipped += 1
                continue
            target = map_target(info.filename)
            if target is None or target in seen:
                skipped += 1
                continue
            seen.add(target)
            selected += 1
            print(f"{'STAGE' if apply else 'PLAN '} {info.filename} -> {target.relative_to(ROOT)}")
            if apply:
                data = z.read(info)
                try:
                    data.decode("utf-8")
                except UnicodeDecodeError:
                    print(f"  SKIP non-UTF8 source: {info.filename}")
                    selected -= 1
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.exists():
                    print(f"  SKIP existing path (won't overwrite): {target.relative_to(ROOT)}")
                    selected -= 1
                    continue
                target.write_bytes(data)
    return selected, skipped


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", type=Path, required=True, help="Original Week 7 V3/V4 service ZIP")
    parser.add_argument("--apply", action="store_true", help="Stage source files after reviewing the plan")
    args = parser.parse_args()
    path = args.zip.expanduser().resolve()
    if not path.is_file():
        parser.error(f"File does not exist: {path}")
    n, skip = inspect_zip(path, args.apply)
    print(f"\nCandidates: {n}; skipped: {skip}")
    print("Important: manually inspect every staged source file for secrets, licensing and paths.")
    print("No artifacts or serialized model files are included. This stage does not make the app runnable.")
    if not args.apply:
        print("Dry run only; rerun with --apply to write files.")


if __name__ == "__main__":
    main()
