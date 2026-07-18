#!/usr/bin/env python3
"""Prep a photo for ASCII conversion: isolate subject, boost local
contrast, composite onto pure white.

Usage: python scripts/prep_photo.py source-photo.jpg
Writes: source-prepped.png (grayscale) next to this repo's root.

Run once per photo — the daily workflow never touches this.
rembg is optional: if it isn't installed (or the photo already has a
clean white background) the script continues without background removal.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

OUT = Path(__file__).resolve().parent.parent / "source-prepped.png"


def remove_background(img: Image.Image) -> Image.Image:
    try:
        from rembg import remove
    except ImportError:
        print("rembg not installed — skipping background removal")
        return img.convert("RGBA")
    return remove(img)


def clahe_gray(img: Image.Image) -> Image.Image:
    """Contrast-limited adaptive histogram equalization — gives a flatly
    lit face real highlights and shadows."""
    gray = np.array(img.convert("L"))
    try:
        import cv2
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        gray = clahe.apply(gray)
    except ImportError:
        from PIL import ImageOps
        print("opencv not installed — falling back to global autocontrast")
        return ImageOps.autocontrast(Image.fromarray(gray), cutoff=1)
    return Image.fromarray(gray)


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(f"usage: {sys.argv[0]} <photo>")
    src = Image.open(sys.argv[1])

    subject = remove_background(src)
    enhanced = clahe_gray(subject)

    # composite onto pure white so the background maps to the blank end
    # of the ASCII ramp (white -> spaces)
    if subject.mode == "RGBA":
        alpha = subject.getchannel("A")
        white = Image.new("L", enhanced.size, 255)
        enhanced = Image.composite(enhanced, white, alpha)

    enhanced.save(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
