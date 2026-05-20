"""
DeepShield — pretrained weights checker / downloader.

Usage:
    python -m backend.ml.weights_downloader

Checks whether fine-tuned FaceForensics++ checkpoint files are present in
MODEL_WEIGHTS_DIR.  If a direct download URL is known the script will fetch
it; otherwise it prints manual-download instructions.

The service runs fine without these files — it falls back to ImageNet
pretrained backbones, which give reasonable (though not FF++-tuned) accuracy.
"""

import logging
import os
import sys
import urllib.request
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Registry of expected weight files
# ---------------------------------------------------------------------------

_WEIGHTS: Dict[str, Dict] = {
    "xception_ff++.pth": {
        "description": "XceptionNet fine-tuned on FaceForensics++ (c23 compression)",
        # No stable public direct-download URL exists for the FF++ Xception weights.
        # Set `url` to a string if you host the file yourself (e.g. on S3).
        "url": None,
        "instructions": (
            "1. Request access at https://github.com/ondyari/FaceForensics\n"
            "2. Download xception-{c23|c40|raw}.p from the provided link\n"
            "3. Convert with:\n"
            "     python -c \"import torch; d=torch.load('xception-c23.p');"
            " torch.save(d, 'ml_models/xception_ff++.pth')\"\n"
            "   OR use the HuggingFace mirror if available:\n"
            "     https://huggingface.co/spaces/otter-ai/FaceForensics"
        ),
    },
    "efficientnet_b4_ff++.pth": {
        "description": "EfficientNet-B4 fine-tuned on FaceForensics++",
        "url": None,
        "instructions": (
            "1. Request access at https://github.com/ondyari/FaceForensics\n"
            "2. Download the EfficientNet-B4 checkpoint from the provided link\n"
            "3. Save as: ml_models/efficientnet_b4_ff++.pth"
        ),
    },
}

# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def _download(url: str, dest: str) -> bool:
    """Download *url* to *dest*. Returns True on success."""
    try:
        print(f"       Downloading {url} …", flush=True)

        def _progress(count, block, total):
            if total > 0:
                pct = min(100, count * block * 100 // total)
                print(f"\r       {pct:3d}%", end="", flush=True)

        urllib.request.urlretrieve(url, dest, reporthook=_progress)
        print()  # newline after progress
        size_mb = os.path.getsize(dest) / 1_048_576
        print(f"       Saved → {dest}  ({size_mb:.1f} MB)")
        return True
    except Exception as exc:
        print(f"\n       Download failed: {exc}")
        try:
            os.remove(dest)
        except OSError:
            pass
        return False


def check_and_download(weights_dir: str) -> None:
    """
    Inspect *weights_dir* for each expected checkpoint.

    For each missing file: attempt an automatic download if a URL is
    configured, otherwise print manual instructions.
    """
    os.makedirs(weights_dir, exist_ok=True)

    all_present = True
    for filename, meta in _WEIGHTS.items():
        path = os.path.join(weights_dir, filename)
        if os.path.exists(path):
            size_mb = os.path.getsize(path) / 1_048_576
            print(f"[OK]   {filename}  ({size_mb:.1f} MB)")
            continue

        all_present = False
        print(f"[MISS] {filename} — {meta['description']}")

        url: Optional[str] = meta.get("url")
        if url:
            _download(url, path)
        else:
            print(f"       Manual download required:\n"
                  f"       {meta['instructions']}\n")

    print()
    if all_present:
        print("All checkpoint files present.")
    else:
        print(
            "One or more checkpoint files are missing.\n"
            "The service will run with ImageNet pretrained weights as fallback.\n"
            "Detection accuracy improves significantly with FF++ fine-tuned weights."
        )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, stream=sys.stdout)
    weights_dir = os.getenv("MODEL_WEIGHTS_DIR", "./ml_models")
    print(f"Checking weights in: {os.path.abspath(weights_dir)}\n")
    check_and_download(weights_dir)
