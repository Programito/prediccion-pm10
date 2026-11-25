"""Build evaluator archives from project files and verified source snapshots."""

import json
from pathlib import Path
import tempfile
from zipfile import ZIP_DEFLATED, ZipFile

from restore_sources import ROOT, digest, inventory, verify


PROJECT_FOLDERS = ("pm10_data", "tests", "scripts", "explorer", "docs", "notebooks", "demo", "models", "data/reference", "data/interim")
SKIP_PARTS = {"__pycache__", "node_modules", "dist", ".pytest_cache"}


def project_files():
    files = {ROOT / "README.md", ROOT / "requirements.txt", ROOT / ".gitignore"}
    for folder in PROJECT_FOLDERS:
        files.update(path for path in (ROOT / folder).rglob("*") if path.is_file() and not SKIP_PARTS.intersection(path.relative_to(ROOT).parts))
    files.update(path for path in (ROOT / "output").rglob("*") if path.is_file() and "delivery" not in path.relative_to(ROOT / "output").parts)
    files.update((ROOT / "data/raw").rglob("*.json"))
    return sorted(files)


def write_archive(path, files):
    with tempfile.NamedTemporaryFile(dir=path.parent, suffix=".zip.part", delete=False) as stream:
        temporary = Path(stream.name)
    try:
        with ZipFile(temporary, "w", compression=ZIP_DEFLATED, compresslevel=6) as archive:
            for file in files:
                archive.write(file, file.relative_to(ROOT).as_posix())
        with ZipFile(temporary) as archive:
            damaged = archive.testzip()
            if damaged:
                raise ValueError(f"Archivo dañado dentro del ZIP: {damaged}")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def main():
    destination = ROOT / "output/delivery"
    destination.mkdir(parents=True, exist_ok=True)
    entries = inventory(ROOT)
    for entry in entries:
        verify(entry)
    bundles = (
        ("pm10_project.zip", project_files()),
        ("pm10_sources.zip", sorted(entry["path"] for entry in entries)),
    )
    report = []
    for name, files in bundles:
        target = destination / name
        write_archive(target, files)
        item = {"file": name, "bytes": target.stat().st_size, "sha256": digest(target), "files": len(files)}
        report.append(item)
        print(f"{name}: {item['bytes'] / 1024**2:.2f} MiB, {len(files)} archivos", flush=True)
    (destination / "checksums.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
