"""
utils/download_data.py — Downloads data files from Google Drive at startup
if they are not already present in the data/ folder.

Called once from utils/data.py before load_data() runs.
Uses requests to stream files, handling Drive's large-file confirmation page.
"""

import zipfile
import requests
from pathlib import Path

DATA_DIR = Path("/data")

GDRIVE_IDS = {
    "pfaf_lev06_merged.zip": "1CwqPEcoHcKlGHSyxNFeqSPpWx_EqMFWw",
    "aqueduct_pfaf_panel_enriched.csv": "1g8Ish1wiLkoUEl3rpZ346pvH4WI6UTK2",
}

SHP_FILE = DATA_DIR / "pfaf_lev06_merged.shp"


def _download(filename: str, file_id: str):
    dest = DATA_DIR / filename
    print(f"Downloading {filename} from Google Drive…")

    session = requests.Session()
    url = "https://drive.google.com/uc"

    resp = session.get(
        url,
        params={"export": "download", "id": file_id},
        stream=True,
        timeout=60,
    )
    resp.raise_for_status()

    # Large files get a virus-scan warning page — Drive sets a confirmation cookie
    token = next(
        (v for k, v in resp.cookies.items() if k.startswith("download_warning")),
        None,
    )
    if token:
        resp = session.get(
            url,
            params={"export": "download", "id": file_id, "confirm": token},
            stream=True,
            timeout=60,
        )
        resp.raise_for_status()

    with open(dest, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1 << 20):  # 1 MB chunks
            if chunk:
                f.write(chunk)

    if not dest.exists() or dest.stat().st_size < 1000:
        raise RuntimeError(f"Download failed or file suspiciously small: {dest}")

    print(f"  ✓ {filename} ({dest.stat().st_size / 1e6:.1f} MB)")


def ensure_data():
    """Download and unzip data files if not already present."""
    print(f"ensure_data() called. DATA_DIR={DATA_DIR}, exists={DATA_DIR.exists()}")
    DATA_DIR.mkdir(exist_ok=True, parents=True)

    csv_path = DATA_DIR / "aqueduct_pfaf_panel_enriched.csv"
    print(f"CSV exists: {csv_path.exists()}")
    if not csv_path.exists():
        print("Downloading CSV...")
        _download("aqueduct_pfaf_panel_enriched.csv", GDRIVE_IDS["aqueduct_pfaf_panel_enriched.csv"])

    if not SHP_FILE.exists():
        print("Downloading shapefile ZIP...")
        zip_path = DATA_DIR / "pfaf_lev06_merged.zip"
        if not zip_path.exists():
            _download("pfaf_lev06_merged.zip", GDRIVE_IDS["pfaf_lev06_merged.zip"])
        print("Extracting shapefile...")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(DATA_DIR)
        zip_path.unlink()  # free up space after extraction
        print("Shapefile extracted.")

    print("ensure_data() complete.")