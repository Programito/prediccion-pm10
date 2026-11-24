"""Verify retained source manifests, optionally downloading missing originals."""

import argparse
import hashlib
import json
from pathlib import Path
import tempfile
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent.parent
MANIFESTS = (
    "data/raw/health_air_history/sources.json",
    "data/raw/health_air_feasibility/sources.json",
    "data/raw/demographics/source.json",
    "data/raw/eea_pm10/sources.json",
)


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def inventory(root):
    entries = []
    for relative in MANIFESTS:
        manifest_path = root / relative
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        source = manifest.get("sources", manifest.get("files", [manifest]))
        values = source.values() if isinstance(source, dict) else source
        for entry in values:
            if entry.get("status", "downloaded") != "downloaded":
                continue
            filename = entry["file"]
            if not filename or "/" in filename or "\\" in filename or filename in {".", ".."}:
                raise ValueError(f"Nombre de archivo incompatible en {relative}")
            path = manifest_path.parent / filename
            url = entry.get("source_url", entry.get("url", ""))
            checksum = entry["sha256"].lower()
            if len(checksum) != 64 or any(char not in "0123456789abcdef" for char in checksum):
                raise ValueError(f"Huella inválida en {relative}")
            entries.append({"path": path, "url": url, "sha256": checksum, "bytes": int(entry["bytes"])})
    if len({entry["path"] for entry in entries}) != len(entries):
        raise ValueError("El inventario repite una ruta.")
    return entries


def verify(entry):
    path = entry["path"]
    if not path.is_file():
        raise FileNotFoundError(f"Falta {path.name}")
    if path.stat().st_size != entry["bytes"] or digest(path) != entry["sha256"]:
        raise ValueError(f"El archivo difiere del original registrado: {path.name}")


def restore(entry):
    path = entry["path"]
    if path.exists():
        verify(entry)
        return
    if not entry["url"].startswith("https://"):
        raise ValueError(f"URL HTTPS ausente: {path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=path.name + ".", suffix=".part", delete=False) as stream:
            temporary = Path(stream.name)
            request = Request(entry["url"], headers={"User-Agent": "TFM-PM10-source-restoration/1.0"})
            with urlopen(request, timeout=60) as response:
                for block in iter(lambda: response.read(1024 * 1024), b""):
                    stream.write(block)
        verify({**entry, "path": temporary})
        # Hard-link publication is atomic and refuses to replace a concurrent file.
        try:
            path.hardlink_to(temporary)
        except FileExistsError:
            verify(entry)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="Raíz de la copia que contiene los manifiestos.")
    parser.add_argument("--download", action="store_true", help="Descargar originales ausentes y comprobarlos antes de publicarlos.")
    parser.add_argument("--file", action="append", default=[], help="Limitar a una ruta del inventario relativa a la raíz.")
    args = parser.parse_args()
    root = args.root.resolve()
    entries = inventory(root)
    if args.file:
        available = {entry["path"].relative_to(root).as_posix(): entry for entry in entries}
        unknown = set(args.file) - available.keys()
        if unknown:
            parser.error("Rutas ajenas al inventario: " + ", ".join(sorted(unknown)))
        entries = [entry for name, entry in available.items() if name in args.file]
    failures = []
    for entry in entries:
        name = entry["path"].relative_to(root).as_posix()
        try:
            if args.download:
                restore(entry)
            else:
                verify(entry)
            print(f"OK {name}", flush=True)
        except (OSError, ValueError) as error:
            failures.append(name)
            print(f"ERROR {name}: {error}", flush=True)
    print(f"Verificados {len(entries) - len(failures)}/{len(entries)} originales.")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
