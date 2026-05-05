"""
utils/download_data.py — Downloads data files from Google Drive at startup
if they are not already present in the data/ folder.

Called once from streamlit_app.py before anything else runs.
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
    url = (
        f"https://drive.usercontent.google.com/download"
        f"?id={file_id}&export=download&authuser=0&confirm=t"
    )

    resp = session.get(url, stream=True, timeout=120)
    resp.raise_for_status()

    content_type = resp.headers.get("Content-Type", "")
    if "text/html" in content_type:
        raise RuntimeError(
            f"Google Drive returned an HTML page instead of {filename}. "
            "Quota may be exceeded or file permissions are wrong."
        )

    with open(dest, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1 << 20):
            if chunk:
                f.write(chunk)

    print(f"  ✓ {filename} ({dest.stat().st_size / 1e6:.1f} MB)")


def ensure_data():
    print(f"ensure_data() called. DATA_DIR={DATA_DIR}, exists={DATA_DIR.exists()}")
    DATA_DIR.mkdir(exist_ok=True, parents=True)

    csv_path = DATA_DIR / "aqueduct_pfaf_panel_enriched.csv"

    # Validate existing CSV — delete if it's a corrupt HTML page
    if csv_path.exists():
        with open(csv_path, "rb") as f:
            head = f.read(512)
        if b"<!DOCTYPE" in head or b"<html" in head or csv_path.stat().st_size < 1_000_000:
            print("CSV is corrupt (HTML page), deleting and re-downloading...")
            csv_path.unlink()

    print(f"CSV exists: {csv_path.exists()}")
    if not csv_path.exists():
        print("Downloading CSV...")
        _download("aqueduct_pfaf_panel_enriched.csv", GDRIVE_IDS["aqueduct_pfaf_panel_enriched.csv"])

    if not SHP_FILE.exists():
        zip_path = DATA_DIR / "pfaf_lev06_merged.zip"

        if zip_path.exists():
            print("Removing previous (possibly corrupt) zip...")
            zip_path.unlink()

        print("Downloading shapefile ZIP...")
        _download("pfaf_lev06_merged.zip", GDRIVE_IDS["pfaf_lev06_merged.zip"])

        print("Extracting shapefile...")
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(DATA_DIR)
            zip_path.unlink()
            print("Shapefile extracted.")
        except zipfile.BadZipFile:
            zip_path.unlink()
            raise RuntimeError(
                "Downloaded zip is corrupt — likely an HTML error page from Drive. "
                "Check file sharing permissions or try again in 24h if quota is exceeded."
            )

    print("ensure_data() complete.")
