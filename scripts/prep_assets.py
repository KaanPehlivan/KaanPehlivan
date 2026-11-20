"""One-time asset prep: subset fonts to small WOFFs and turn the portrait into ASCII.

Run locally (not in CI): uv run --with fonttools --with pillow python scripts/prep_assets.py <font_dir> <portrait.jpg> <mask.png>
mask.png comes from: swift scripts/person_mask.swift <portrait.jpg> <mask.png>
font_dir holds Google Fonts' InstrumentSerif-Regular/Italic.ttf, Geist[wght].ttf, GeistMono[wght].ttf (SIL OFL).
"""
import os
import sys

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from PIL import Image, ImageOps

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
CHARS = "".join(chr(c) for c in range(32, 127)) + "ıİşŞğĞüÜöÖçÇâ’‘“”–—·•→↗×…"
RAMP = " .:-=+*#%@"  # dark -> bright

def make_font(src, out, wght=None):
    font = TTFont(src)
    if wght:
        font = instancer.instantiateVariableFont(font, {"wght": wght})
    opts = subset.Options()
    opts.flavor = "woff"
    opts.layout_features = ["kern", "liga"]
    sub = subset.Subsetter(opts)
    sub.populate(text=CHARS)
    sub.subset(font)
    font.flavor = "woff"
    font.save(out)
    missing = [c for c in "↗→·" if ord(c) not in font.getBestCmap()]
    print(f"{os.path.basename(out)}: {os.path.getsize(out)} bytes, missing {missing}")

def make_ascii(photo, mask, out, cols=72):
    img, msk = Image.open(photo).convert("L"), Image.open(mask).convert("L")
    w, h = img.size
    box = (int(w * .26), int(h * .06), int(w * .74), int(h * .42))  # head and shoulders
    img = ImageOps.autocontrast(img.crop(box), cutoff=2).point(lambda v: int(255 * (v / 255) ** 1.6))
    rows = int(cols * img.height / img.width * .5)  # mono glyphs are ~2x taller than wide
    img, msk = img.resize((cols, rows)), msk.crop(box).resize((cols, rows))
    px, mk = img.load(), msk.load()
    # the person mask keeps dark hair and clothes as faint texture and blanks the background
    idx = lambda x, y: max(1, min(len(RAMP) - 1, px[x, y] * len(RAMP) // 256)) if mk[x, y] > 127 else 0
    lines = ["".join(RAMP[idx(x, y)] for x in range(cols)).rstrip() for y in range(rows)]
    open(out, "w").write("\n".join(lines) + "\n")
    print(f"portrait: {cols}x{rows}")

if __name__ == "__main__":
    src, photo = sys.argv[1], sys.argv[2]
    f = lambda n: os.path.join(ROOT, "fonts", n)
    make_font(os.path.join(src, "InstrumentSerif-Regular.ttf"), f("serif.woff"))
    make_font(os.path.join(src, "InstrumentSerif-Italic.ttf"), f("serif-italic.woff"))
    make_font(os.path.join(src, "Geist[wght].ttf"), f("sans.woff"), 400)
    make_font(os.path.join(src, "Geist[wght].ttf"), f("sans-600.woff"), 600)
    make_font(os.path.join(src, "GeistMono[wght].ttf"), f("mono.woff"), 400)
    make_ascii(photo, sys.argv[3], os.path.join(ROOT, "data", "portrait.txt"))
