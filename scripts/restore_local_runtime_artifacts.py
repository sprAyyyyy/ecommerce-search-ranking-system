"""Restore local-only Week 7 runtime artifacts from an original project ZIP.

No broad extraction; the six selected artifacts are only written to app/artifacts/,
which is ignored by git. Use only on your own trusted archive.
"""
import argparse
import io
import zipfile
from pathlib import Path

FILES = (
    "runtime_config.json", "lambdamart_model.txt",
    "sbert_product_embeddings.npy", "catalog.parquet",
    "clip_embedding_map.csv", "clip_image_embeddings.npy",
)

parser = argparse.ArgumentParser()
parser.add_argument("--source", type=Path, required=True, help="Original amazon internship.zip or week7_v4_final_package.zip")
args = parser.parse_args()
archive = args.source.expanduser()
if not archive.is_file():
    parser.error(f"File not found: {archive}")

with zipfile.ZipFile(archive) as top:
    nested = [n for n in top.namelist() if n.lower().endswith("amazon_week7_v4_final_package.zip")]
    if nested:
        if len(nested) != 1:
            parser.error("Ambiguous nested Week 7 package")
        inner = zipfile.ZipFile(io.BytesIO(top.read(nested[0])))
    else:
        inner = top
    with inner:
        needed = {f: f"artifacts/{f}" for f in FILES}
        missing = [p for p in needed.values() if p not in inner.namelist()]
        if missing:
            parser.error(f"Missing artifacts: {missing}")
        out = Path(__file__).resolve().parents[1] / "app" / "artifacts"
        out.mkdir(parents=True, exist_ok=True)
        for file, member in needed.items():
            data = inner.read(member)
            dest = out / file
            dest.write_bytes(data)
            print(f"Restored locally: {dest} ({len(data):,} bytes)")
print("Local artifact restore complete. Do not commit app/artifacts/ to the public repository.")
