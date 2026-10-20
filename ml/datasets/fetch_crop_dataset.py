"""
Download the Crop Recommendation Dataset (Atharva Ingle, Kaggle, Apache 2.0 licence).

Usage (from the project root):
    python ml/datasets/fetch_crop_dataset.py

If the public download endpoint asks for authentication, download the zip manually from
https://www.kaggle.com/datasets/atharvaingle/crop-recommendation-dataset and place
Crop_recommendation.csv in ml/datasets/crop_recommendation/.
"""

import io
import ssl
import urllib.request
import zipfile
from pathlib import Path

URL = "https://www.kaggle.com/api/v1/datasets/download/atharvaingle/crop-recommendation-dataset"
OUT_DIR = Path(__file__).resolve().parent / "crop_recommendation"

# OS certificate store; strict X.509 mode disabled for campus/office TLS-inspection proxies.
SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.verify_flags &= ~getattr(ssl, "VERIFY_X509_STRICT", 0)


def main():
    req = urllib.request.Request(URL, headers={"User-Agent": "KrishiVeda-dataset-fetch/1.0 (academic project)"})
    with urllib.request.urlopen(req, timeout=120, context=SSL_CONTEXT) as resp:
        data = resp.read()
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUT_DIR / "Crop_recommendation.csv").write_bytes(zf.read("Crop_recommendation.csv"))
    print(f"Saved {OUT_DIR / 'Crop_recommendation.csv'}")


if __name__ == "__main__":
    main()
