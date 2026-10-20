"""
Download a balanced subset of the PlantVillage dataset without fetching the whole archive.

Source  : "Data for: Identification of Plant Leaf Diseases Using a 9-layer Deep CNN"
          (Arun Pandian J., Geetharamani G.), Mendeley Data, doi:10.17632/tywbtsjrjv.1
          Original images: Hughes & Salathe, "An open access repository of images on plant
          health..." (arXiv:1511.08060).
License : CC0 1.0 (as listed on the Mendeley record).

The archive is ~868 MB. Instead of downloading all of it, this script uses HTTP range
requests: it reads the zip's central directory (the "table of contents" at the end of the
file), picks up to N random images per class, and downloads only those images.

Usage (from the project root):
    python ml/datasets/fetch_plantvillage_subset.py --per-class 250
"""

import argparse
import concurrent.futures
import http.client
import io
import json
import random
import re
import ssl
import struct
import time
import urllib.request
import zipfile
import zlib
from pathlib import Path

DATASET_URL = (
    "https://data.mendeley.com/public-files/datasets/tywbtsjrjv/files/"
    "d5652a28-c1d8-4b76-97f3-72fb80f94efc/file_downloaded"
)
ROOT_FOLDER = "Plant_leave_diseases_dataset_without_augmentation"
DEFAULT_OUT = Path(__file__).resolve().parent / "plantvillage_subset"

# Use the operating system's trusted certificates. Python 3.13+ enables strict X.509
# checks by default, which reject some network-inspection proxies' CA certificates
# (e.g. campus/office firewalls). The chain and hostname are still fully verified.
SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.verify_flags &= ~getattr(ssl, "VERIFY_X509_STRICT", 0)
USER_AGENT = "KrishiVeda-dataset-fetch/1.0 (academic project)"


def http_range(url: str, start: int, end: int, retries: int = 4) -> bytes:
    """Fetch bytes [start, end] (inclusive) from url, retrying on dropped connections."""
    for attempt in range(retries):
        try:
            return _http_range_once(url, start, end)
        except (OSError, http.client.HTTPException):
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)


def _http_range_once(url: str, start: int, end: int) -> bytes:
    req = urllib.request.Request(url, headers={"Range": f"bytes={start}-{end}", "User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60, context=SSL_CONTEXT) as resp:
        if resp.status != 206:
            raise RuntimeError(f"Server did not honour range request (HTTP {resp.status})")
        return resp.read()


def resolve_url(url: str) -> tuple[str, int]:
    """Follow the Mendeley redirect once and return (final_url, total_size)."""
    req = urllib.request.Request(url, headers={"Range": "bytes=0-0", "User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60, context=SSL_CONTEXT) as resp:
        total = int(resp.headers["Content-Range"].split("/")[-1])
        return resp.geturl(), total


class RemoteZipFile(io.RawIOBase):
    """Minimal read-only, seekable file object backed by HTTP range requests.

    Only the tail of the archive (central directory) is cached; that is all
    zipfile.ZipFile needs in order to list the members.
    """

    def __init__(self, url: str, size: int, tail_bytes: int = 12 * 1024 * 1024):
        self.url, self.size, self.pos = url, size, 0
        self.tail_start = max(0, size - tail_bytes)
        self.tail = http_range(url, self.tail_start, size - 1)

    def seekable(self):
        return True

    def readable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, offset, whence=io.SEEK_SET):
        base = {io.SEEK_SET: 0, io.SEEK_CUR: self.pos, io.SEEK_END: self.size}[whence]
        self.pos = base + offset
        return self.pos

    def read(self, n=-1):
        if n is None or n < 0:
            n = self.size - self.pos
        end = min(self.pos + n, self.size)
        if self.pos >= self.tail_start:
            data = self.tail[self.pos - self.tail_start : end - self.tail_start]
        else:
            data = http_range(self.url, self.pos, end - 1) if end > self.pos else b""
        self.pos = end
        return data


def download_member(url: str, info: zipfile.ZipInfo) -> bytes:
    """Download one member using its local header offset and decompress it."""
    # Local header is 30 bytes + file name + extra field. The local extra field length
    # can differ from the central directory one, so over-fetch slightly and parse.
    approx = 30 + len(info.orig_filename.encode("utf-8")) + 1024 + info.compress_size
    blob = http_range(url, info.header_offset, info.header_offset + approx)
    sig, = struct.unpack("<I", blob[:4])
    if sig != 0x04034B50:
        raise ValueError(f"Bad local header for {info.filename}")
    name_len, extra_len = struct.unpack("<HH", blob[26:30])
    start = 30 + name_len + extra_len
    raw = blob[start : start + info.compress_size]
    if info.compress_type == zipfile.ZIP_STORED:
        data = raw
    elif info.compress_type == zipfile.ZIP_DEFLATED:
        data = zlib.decompress(raw, -15)
    else:
        raise ValueError(f"Unsupported compression {info.compress_type}")
    if zlib.crc32(data) & 0xFFFFFFFF != info.CRC:
        raise ValueError(f"CRC mismatch for {info.filename}")
    return data


def safe_dir_name(label: str) -> str:
    return re.sub(r"[^A-Za-z0-9_()\-]", "_", label)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--per-class", type=int, default=250, help="max images per class")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--workers", type=int, default=16)
    args = parser.parse_args()

    url, size = resolve_url(DATASET_URL)
    print(f"Archive size: {size / 1e6:.1f} MB. Reading table of contents...")
    zf = zipfile.ZipFile(RemoteZipFile(url, size))

    by_class: dict[str, list[zipfile.ZipInfo]] = {}
    for info in zf.infolist():
        parts = info.filename.split("/")
        if len(parts) == 3 and parts[0] == ROOT_FOLDER and parts[2].lower().endswith((".jpg", ".jpeg", ".png")):
            by_class.setdefault(parts[1], []).append(info)
    print(f"Found {sum(map(len, by_class.values()))} images in {len(by_class)} classes")

    rng = random.Random(args.seed)
    jobs = []
    for label, members in sorted(by_class.items()):
        chosen = rng.sample(members, min(args.per_class, len(members)))
        for info in chosen:
            dest = args.out / safe_dir_name(label) / Path(info.filename).name
            if not dest.exists():
                jobs.append((label, info, dest))

    print(f"Downloading {len(jobs)} images with {args.workers} workers...")
    done = 0

    def work(job):
        _, info, dest = job
        data = download_member(url, info)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)

    with concurrent.futures.ThreadPoolExecutor(args.workers) as pool:
        for fut in concurrent.futures.as_completed([pool.submit(work, j) for j in jobs]):
            fut.result()
            done += 1
            if done % 500 == 0:
                print(f"  {done}/{len(jobs)}")

    manifest = {
        "source": "Mendeley Data doi:10.17632/tywbtsjrjv.1 (PlantVillage, without augmentation)",
        "license": "CC0 1.0",
        "per_class_limit": args.per_class,
        "seed": args.seed,
        "classes": {
            safe_dir_name(label): {
                "original_label": label,
                "available": len(members),
                "downloaded": len(list((args.out / safe_dir_name(label)).glob("*"))),
            }
            for label, members in sorted(by_class.items())
        },
    }
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"Done. Subset saved to {args.out}")


if __name__ == "__main__":
    main()
