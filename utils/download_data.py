"""
utils/download_data.py — Downloads data files from Google Drive at startup
if they are not already present in the data/ folder.

Called once from utils/data.py before load_data() runs.
Uses gdown which handles Google Drive's large-file virus-scan bypass.
"""

import zipfile
from pathlib import Path

import os
DATA_DIR = Path("/data")

# Google Drive file IDs
GDRIVE_IDS = {
    "pfaf_lev06_merged.zip": "1CwqPEcoHcKlGHSyxNFeqSPpWx_EqMFWw",
    "aqueduct_pfaf_panel_enriched.csv": "1g8Ish1wiLkoUEl3rpZ346pvH4WI6UTK2",
}

# After unzipping, we expect this file to exist
SHP_FILE = DATA_DIR / "pfaf_lev06_merged.shp"


def _download(filename: str, file_id: str):
    try:
        import gdown
    except ImportError:
        raise SystemExit("gdown is required. Add it to requirements.txt and reinstall.")

    dest = DATA_DIR / filename
    print(f"Downloading {filename} from Google Drive…")
    gdown.download(id=file_id, output=str(dest), quiet=False, fuzzy=True)
    if not dest.exists():
        raise RuntimeError(f"Download failed: {dest} not found after gdown.")
    print(f"  ✓ {filename}")


def ensure_data():
    """Download and unzip data files if not already present. Safe to call multiple times."""
    DATA_DIR.mkdir(exist_ok=True)

    # --- CSV ---
    csv_path = DATA_DIR / "aqueduct_pfaf_panel_enriched.csv"
    if not csv_path.exists():
        _download("aqueduct_pfaf_panel_enriched.csv", GDRIVE_IDS["aqueduct_pfaf_panel_enriched.csv"])

    # --- Shapefile (zipped) ---
    if not SHP_FILE.exists():
        zip_path = DATA_DIR / "pfaf_lev06_merged.zip"
        if not zip_path.exists():
            _download("pfaf_lev06_merged.zip", GDRIVE_IDS["pfaf_lev06_merged.zip"])
        print("Extracting shapefile…")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(DATA_DIR)
        print("  ✓ shapefile extracted")

    print("Data ready.")