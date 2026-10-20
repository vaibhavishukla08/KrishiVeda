"""
Download the PlantDoc dataset (real-field leaf photos) and map it to KrishiVeda's classes.

Source  : Singh et al., "PlantDoc: A Dataset for Visual Plant Disease Detection", CoDS-COMAD 2020
          https://github.com/pratikkayal/PlantDoc-Dataset
Licence : CC BY 4.0 (attribution required — keep this notice and cite the paper)

PlantDoc images are photos taken in fields and gardens or collected from the web: cluttered
backgrounds, several leaves, different lighting. They are what a farmer's phone photo looks like,
unlike PlantVillage's single leaf on a plain background.

Images are resized so the longer side is at most 512 px (the CNN uses 224 px) to save disk space,
and saved to ml/datasets/plantdoc/<train|test>/<KrishiVeda class>/.

Usage (from the project root):
    python ml/datasets/fetch_plantdoc.py
    python ml/datasets/fetch_plantdoc.py --list-only   # show image counts per class
"""

import argparse
import concurrent.futures
import io
import json
import ssl
import subprocess
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image, UnidentifiedImageError

REPO = "pratikkayal/PlantDoc-Dataset"
BRANCH = "master"
OUT = Path(__file__).resolve().parent / "plantdoc"
MAX_SIDE = 512

# PlantDoc folder name -> KrishiVeda (PlantVillage) class name
CLASS_MAP = {
    "Apple Scab Leaf": "Apple___Apple_scab",
    "Apple leaf": "Apple___healthy",
    "Apple rust leaf": "Apple___Cedar_apple_rust",
    "Bell_pepper leaf spot": "Pepper__bell___Bacterial_spot",
    "Bell_pepper leaf": "Pepper__bell___healthy",
    "Blueberry leaf": "Blueberry___healthy",
    "Cherry leaf": "Cherry___healthy",
    "Corn Gray leaf spot": "Corn___Cercospora_leaf_spot_Gray_leaf_spot",
    "Corn leaf blight": "Corn___Northern_Leaf_Blight",
    "Corn rust leaf": "Corn___Common_rust",
    "Peach leaf": "Peach___healthy",
    "Potato leaf early blight": "Potato___Early_blight",
    "Potato leaf late blight": "Potato___Late_blight",
    "Raspberry leaf": "Raspberry___healthy",
    "Soyabean leaf": "Soybean___healthy",
    "Squash Powdery mildew leaf": "Squash___Powdery_mildew",
    "Strawberry leaf": "Strawberry___healthy",
    "Tomato Early blight leaf": "Tomato___Early_blight",
    "Tomato Septoria leaf spot": "Tomato___Septoria_leaf_spot",
    "Tomato leaf bacterial spot": "Tomato___Bacterial_spot",
    "Tomato leaf late blight": "Tomato___Late_blight",
    "Tomato leaf mosaic virus": "Tomato___Tomato_mosaic_virus",
    "Tomato leaf yellow virus": "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato leaf": "Tomato___healthy",
    "Tomato mold leaf": "Tomato___Leaf_Mold",
    "Tomato two spotted spider mites leaf": "Tomato___Spider_mites_Two-spotted_spider_mite",
    "grape leaf black rot": "Grape___Black_rot",
    "grape leaf": "Grape___healthy",
}

# OS certificate store; strict X.509 mode disabled for campus/office TLS-inspection proxies.
SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.verify_flags &= ~getattr(ssl, "VERIFY_X509_STRICT", 0)
HEADERS = {"User-Agent": "KrishiVeda-dataset-fetch/1.0 (academic project)"}


def get(url: str, retries: int = 5) -> bytes:
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=90, context=SSL_CONTEXT) as resp:
                return resp.read()
        except OSError:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)


def list_repo_files() -> list[str]:
    """List file paths with a shallow, blob-less git clone (downloads names only, not images).

    This avoids GitHub's 60-requests/hour API limit for unauthenticated users.
    """
    with tempfile.TemporaryDirectory() as tmp:
        url = f"https://github.com/{REPO}.git"
        clone = ["clone", "--quiet", "--filter=blob:none", "--no-checkout", "--depth", "1", "--branch", BRANCH, url, tmp]
        try:
            subprocess.run(["git", *clone], check=True, capture_output=True, timeout=300)
        except subprocess.CalledProcessError:
            # Windows behind a TLS-inspecting proxy: use the Windows certificate store
            print("git clone failed; retrying with the Windows certificate store (schannel)")
            subprocess.run(["git", "-c", "http.sslBackend=schannel", "-c", "http.schannelCheckRevoke=false", *clone],
                           check=True, capture_output=True, timeout=300)
        out = subprocess.run(["git", "-C", tmp, "ls-tree", "-r", "--name-only", "HEAD"],
                             check=True, capture_output=True, text=True, encoding="utf-8").stdout
    return out.splitlines()


def save_resized(raw: bytes, dest: Path) -> bool:
    try:
        with Image.open(io.BytesIO(raw)) as img:
            img = img.convert("RGB")
            img.thumbnail((MAX_SIDE, MAX_SIDE))
            dest.parent.mkdir(parents=True, exist_ok=True)
            img.save(dest, "JPEG", quality=92)
        return True
    except (UnidentifiedImageError, OSError):
        return False  # a few files in the repo are not valid images


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list-only", action="store_true")
    ap.add_argument("--workers", type=int, default=12)
    args = ap.parse_args()

    paths = list_repo_files()
    jobs = []
    for split in ("train", "test"):
        for folder, cls in CLASS_MAP.items():
            files = sorted(p for p in paths if p.startswith(f"{split}/{folder}/") and p.lower().endswith((".jpg", ".jpeg", ".png")))
            for i, path in enumerate(files):
                jobs.append((path, OUT / split / cls / f"pd_{i:04d}.jpg"))
            print(f"{split:5s} {folder:40s} {len(files):4d}")
    print(f"{len(jobs)} images listed")
    if args.list_only:
        return

    todo = [(p, d) for p, d in jobs if not d.exists()]
    print(f"Downloading {len(todo)} images...")
    done = bad = 0

    def work(job):
        path, dest = job
        url = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{urllib.parse.quote(path)}"
        return save_resized(get(url), dest)

    with concurrent.futures.ThreadPoolExecutor(args.workers) as pool:
        for ok in pool.map(work, todo):
            done += 1
            bad += not ok
            if done % 200 == 0:
                print(f"  {done}/{len(todo)}", flush=True)

    counts = {split: {cls: len(list((OUT / split / cls).glob("*.jpg"))) for cls in sorted(set(CLASS_MAP.values()))}
              for split in ("train", "test")}
    (OUT / "manifest.json").write_text(json.dumps({
        "source": f"https://github.com/{REPO}",
        "citation": "Singh D. et al., PlantDoc: A Dataset for Visual Plant Disease Detection, CoDS-COMAD 2020",
        "license": "CC BY 4.0",
        "class_map": CLASS_MAP,
        "max_side_px": MAX_SIDE,
        "unreadable_files_skipped": bad,
        "counts": counts,
    }, indent=2))
    print(f"Done. {bad} unreadable files skipped. Saved to {OUT}")


if __name__ == "__main__":
    main()
