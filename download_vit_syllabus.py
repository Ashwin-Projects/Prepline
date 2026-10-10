"""Download the official VIT CSE 2024-25 syllabus PDF without modifying it.

Run from repository root:
    python scripts/download_vit_syllabus.py
"""
from pathlib import Path
from urllib.request import Request, urlopen
import hashlib

URL = "https://vit.ac.in/wp-content/uploads/2024/08/B.Tech_CSE_2024_2025.pdf"
DEST = Path(__file__).resolve().parents[1] / "data" / "raw" / "syllabi" / "VIT_CSE_2024_2025.pdf"

def main():
    DEST.parent.mkdir(parents=True, exist_ok=True)
    request = Request(URL, headers={"User-Agent": "Prepline-research/1.0 (curriculum source retrieval)"})
    with urlopen(request, timeout=60) as response:
        content_type = response.headers.get("Content-Type", "")
        data = response.read()
    if not data.startswith(b"%PDF-"):
        raise RuntimeError(f"Official URL did not return a PDF (Content-Type: {content_type})")
    DEST.write_bytes(data)
    print(f"Saved {DEST} ({len(data):,} bytes)")
    print(f"SHA-256: {hashlib.sha256(data).hexdigest()}")
    print("Next: verify text-selectability and record this checksum in the ingestion manifest.")

if __name__ == "__main__":
    main()
