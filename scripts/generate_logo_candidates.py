# -*- coding: utf-8 -*-
"""Cloudy Canvas - logo candidate generator.

All marks are drawn in code with Pillow. No stock art, no AI.

Run from the project root:  python3 scripts/generate_logo_candidates.py
Writes 512px transparent masters + a contact sheet to assets/logo-candidates/.

Art direction
- one shared stylised cloud silhouette (`cloud`): 4 bottom-anchored bumps on a
  straight base. The base rect ends are inscribed in the outer bumps (base end
  radius == base half height), so the silhouette never shows an elbow corner and
  sub(cloud(grow=t), cloud(0)) is an outline of uniform thickness t.
- three cloud treatments (uniform monoline, light/dark slice, dot dissolve) and
  three marks that drop the cloud and lean on paint / canvas.
"""

import math
import os

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

S = 256          # logical canvas
SS = 4           # supersampling factor (draw at 1024, downscale to 512)
W = S * SS
OUT_DIR = os.path.join("store-assets", "logo-candidates")

LIGHT_BG = "#F4EEFF"
DARK_BG = "#180F2A"

PALETTES = {
    "light": {
        "top": "#A6B1E1", "bot": "#6E7CBE", "ink": "#303A86",
        "soft": "#C7BEE9", "lite_a": "#CFC8EE", "lite_b": "#A6B1E1",
        "back": "#303A86", "bg": LIGHT_BG,
    },
    "dark": {
        "top": "#9AA4E0", "bot": "#717CCC", "ink": "#EDEFF7",
        "soft": "#454B7A", "lite_a": "#A6B1E1", "lite_b": "#717CCC",
        "back": "#3F4573", "bg": DARK_BG,
    },
}

CLEAR = (0, 0, 0, 0)


# ------------------------------------------------------------------ helpers
def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def layer():
    return Image.new("RGBA", (W, W), CLEAR)


def blank():
    return Image.new("L", (W, W), 0)


def ell(cx, cy, r, ry=None):
    ry = r if ry is None else ry
    m = blank()
    ImageDraw.Draw(m).ellipse(
        [(cx - r) * SS, (cy - ry) * SS, (cx + r) * SS, (cy + ry) * SS], fill=255)
    return m


def rrect(x0, y0, x1, y1, r):
    m = blank()
    r = max(0.0, min(r, (x1 - x0) / 2 - 0.5, (y1 - y0) / 2 - 0.5))
    ImageDraw.Draw(m).rounded_rectangle(
        [x0 * SS, y0 * SS, x1 * SS, y1 * SS], radius=r * SS, fill=255)
    return m


def poly(pts):
    m = blank()
    ImageDraw.Draw(m).polygon([(x * SS, y * SS) for x, y in pts], fill=255)
    return m


def uni(*ms):
    out = ms[0]
    for m in ms[1:]:
        out = ImageChops.lighter(out, m)
    return out


def sub(a, b):
    return ImageChops.subtract(a, b)


def inter(a, b):
    return ImageChops.darker(a, b)


def all_inside(mask, cx, cy, r, n=18, pad=3.0):
    """True when a disc of radius r around (cx, cy) sits fully inside `mask`."""
    if not (0 <= cx < S and 0 <= cy < S):
        return False
    if mask.getpixel((int(cx * SS), int(cy * SS))) < 250:
        return False
    for i in range(n):
        a = 2.0 * math.pi * i / n
        x = int((cx + (r + pad) * math.cos(a)) * SS)
        y = int((cy + (r + pad) * math.sin(a)) * SS)
        if not (0 <= x < W and 0 <= y < W):
            return False
        if mask.getpixel((x, y)) < 250:
            return False
    return True


def grad(c0, c1, angle=90.0):
    sw = sh = 96
    a = math.radians(angle)
    dx, dy = math.cos(a), math.sin(a)
    ps = [x * dx + y * dy for x in (0, sw - 1) for y in (0, sh - 1)]
    lo, hi = min(ps), max(ps)
    im = Image.new("RGB", (sw, sh))
    px = im.load()
    r0, g0, b0 = rgb(c0)
    r1, g1, b1 = rgb(c1)
    for y in range(sh):
        for x in range(sw):
            t = ((x * dx + y * dy) - lo) / (hi - lo)
            px[x, y] = (round(r0 + (r1 - r0) * t),
                        round(g0 + (g1 - g0) * t),
                        round(b0 + (b1 - b0) * t))
    return im.resize((W, W), Image.BICUBIC)


def stamp(base, mask, color=None, gradient=None, angle=90.0, alpha=255):
    if gradient is not None:
        src = grad(gradient[0], gradient[1], angle).convert("RGBA")
        if alpha < 255:
            src.putalpha(src.getchannel("A").point(lambda v: v * alpha // 255))
    else:
        src = Image.new("RGBA", (W, W), rgb(color) + (alpha,))
    return Image.alpha_composite(base, Image.composite(src, layer(), mask))


# bumps: (x offset in width units, radius in width units), all tangent to the base
BUMPS = ((-0.348, 0.152), (-0.106, 0.2848), (0.207, 0.212), (0.394, 0.106))
BASE_R = 0.076          # base half height == base end radius -> ends stay inside


def cloud(cx, cy, width, grow=0.0):
    """Stylised cloud: bumpy top, straight base. `grow` is a true Minkowski
    offset: base ends stay inscribed in the outer bumps, so rings come out with
    a uniform thickness and no corner artefacts."""
    yb = cy + width * 0.5695 / 2.0
    rad = BASE_R * width + grow
    m = blank()
    d = ImageDraw.Draw(m)
    for dxf, rf in BUMPS:
        r0 = rf * width
        r = r0 + grow
        cxx = cx + dxf * width
        cyy = yb - r0
        d.ellipse([(cxx - r) * SS, (cyy - r) * SS, (cxx + r) * SS, (cyy + r) * SS], fill=255)
    d.rounded_rectangle(
        [(cx - 0.348 * width - BASE_R * width - grow) * SS, (yb - 0.152 * width) * SS,
         (cx + 0.394 * width + BASE_R * width + grow) * SS, (yb + grow) * SS],
        radius=rad * SS, fill=255)
    return m


def soft(mask, radius=2.0, cut=145):
    """Blur + threshold: rounds off the hair-thin fillet spurs of an offset ring."""
    return mask.filter(ImageFilter.GaussianBlur(radius)).point(
        lambda v: 255 if v > cut else 0)


# ------------------------------------------------------------------ designs
def d_monoline(p):
    """01 - the cloud as a single uniform monoline outline."""
    img = layer()
    ring = sub(cloud(126, 112, 172, grow=13.0), cloud(126, 112, 172))
    return stamp(img, soft(ring), gradient=(p["ink"], p["bot"]), angle=125)


def d_slice(p):
    """02 - cloud sliced into a light half and a dark half (light/dark themes)."""
    img = layer()
    body = cloud(126, 104, 172)
    left = poly([(-400, -400), (126, -400), (152, 400), (-400, 400)])
    right = poly([(134, -400), (500, -400), (500, 400), (160, 400)])
    img = stamp(img, sub(body, right), gradient=(p["lite_a"], p["lite_b"]), angle=120)
    return stamp(img, sub(body, left), color=p["ink"])


def d_dissolve(p):
    """03 - cloud dissolving from a solid left half into a dot matrix."""
    img = layer()
    r = 6.5
    body = cloud(126, 106, 172)
    dot_side = poly([(106, -300), (300, -300), (300, 400), (146, 400)])
    solid = sub(body, dot_side)
    dots = blank()
    dd = ImageDraw.Draw(dots)
    for gx in range(2, S - 4, 19):
        for gy in range(2, S - 4, 19):
            if all_inside(body, gx, gy, r + 6.0):
                dd.ellipse([(gx - r) * SS, (gy - r) * SS,
                            (gx + r) * SS, (gy + r) * SS], fill=255)
    img = stamp(img, solid, gradient=(p["top"], p["bot"]), angle=120)
    return stamp(img, inter(dots, dot_side), color=p["bot"])


def d_drop(p):
    """04 - a paint drop with a second small drop (no cloud)."""
    img = layer()
    cx, cy, r = 122, 154, 62
    apex = (cx, 34)
    d = cy - apex[1]
    phi = math.acos(r / d)
    tx, ty = r * math.sin(phi), cy - r * math.cos(phi)
    drop = uni(ell(cx, cy, r), poly([apex, (cx - tx, ty), (cx + tx, ty)]))
    img = stamp(img, drop, gradient=(p["top"], p["bot"]), angle=110)
    sm = uni(ell(184, 62, 14), poly([(184, 38), (171, 60), (197, 60)]))
    return stamp(img, sm, color=p["ink"])


def d_stack(p):
    """05 - three stacked canvas cards (no cloud)."""
    img = layer()
    for x, y, fill in ((56, 56, p["bot"]), (74, 74, p["ink"])):
        img = stamp(img, rrect(x, y, x + 96, y + 96, 26), color=fill)
    return stamp(img, rrect(92, 92, 188, 188, 26),
                 gradient=(p["soft"], p["top"]), angle=120)


def d_dabs(p):
    """06 - three paint dabs stepping down the diagonal (no cloud)."""
    img = layer()
    img = stamp(img, ell(86, 88, 42), gradient=(p["ink"], p["bot"]), angle=120)
    img = stamp(img, ell(162, 142, 30), color=p["bot"])
    return stamp(img, ell(100, 192, 21), color=p["top"])


def d_shadow(p):
    """07 - cloud with a hard offset shadow (solid, punchy)."""
    img = layer()
    img = stamp(img, cloud(118, 104, 168), color=p["back"])
    return stamp(img, cloud(104, 92, 168), gradient=(p["top"], p["bot"]), angle=120)


DESIGNS = [
    ("01-monoline", d_monoline),
    ("02-slice", d_slice),
    ("03-dissolve", d_dissolve),
    ("04-drop", d_drop),
    ("05-stack", d_stack),
    ("06-dabs", d_dabs),
    ("07-shadow", d_shadow),
]

# the mark the user picked, shipped transparent at 512 + as the 128px extension icon
CHOSEN = "05-stack"


# ------------------------------------------------------------------ output
def save_master(img, name):
    os.makedirs(OUT_DIR, exist_ok=True)
    img.resize((512, 512), Image.LANCZOS).save(os.path.join(OUT_DIR, name + ".png"))


def font(size, bold=False):
    path = r"C:\Windows\Fonts\%s.ttf" % ("segoeuib" if bold else "segoeui")
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def contact_sheet(rendered):
    name_w, cell_w, row_h, head_h = 200, 232, 224, 58
    sheet = Image.new("RGB", (name_w + 4 * cell_w, head_h + row_h * len(DESIGNS)), "#FFFFFF")
    d = ImageDraw.Draw(sheet)
    f_head, f_name, f_sub = font(17, True), font(19, True), font(13)
    heads = [("LIGHT UI", "light", LIGHT_BG), ("DARK UI", "dark", DARK_BG),
             ("LIGHT UI - SMALL", "light", LIGHT_BG), ("DARK UI - SMALL", "dark", DARK_BG)]
    for i, (title, _, _) in enumerate(heads):
        d.text((name_w + i * cell_w + 16, 20), title, font=f_head, fill="#333333")
    for r, (slug, _) in enumerate(DESIGNS):
        y = head_h + r * row_h
        d.line([(0, y), (sheet.width, y)], fill="#E4E4E4")
        d.text((16, y + 96), slug, font=f_name, fill="#1B1B1F")
        d.text((16, y + 122), "512px master, transparent", font=f_sub, fill="#7A7A7A")
        for c, (_, variant, bg) in enumerate(heads):
            x = name_w + c * cell_w
            d.rounded_rectangle([x + 10, y + 12, x + cell_w - 10, y + row_h - 12],
                                radius=12, fill=bg)
            cx, cy = x + cell_w // 2, y + row_h // 2
            big = 176 if c < 2 else 64
            src = rendered[(slug, variant)]
            im = src.resize((big, big), Image.LANCZOS)
            sheet.paste(im, (cx - big // 2, cy - big // 2 - (0 if c < 2 else 26)), im)
            if c >= 2:
                tiny = src.resize((32, 32), Image.LANCZOS)
                sheet.paste(tiny, (cx + big // 2 + 10, cy + 4), tiny)
                d.text((cx - big // 2 - 14, cy + big // 2 - 4), "64 / 32 px", font=f_sub,
                       fill="#8C8C8C" if c == 2 else "#7C86BE")
    out = os.path.join(OUT_DIR, "contact-sheet.png")
    sheet.save(out)
    return out


def checker(size, cell=16):
    """Transparency checkerboard - proves the mark really has no background."""
    im = Image.new("RGB", (size, size), "#FFFFFF")
    d = ImageDraw.Draw(im)
    for y in range(0, size, cell):
        for x in range(0, size, cell):
            if (x // cell + y // cell) % 2:
                d.rectangle([x, y, x + cell - 1, y + cell - 1], fill="#E2E2EA")
    return im


def chosen_preview(img):
    cols = [("256 px", 256), ("128 px", 128), ("64 px", 64), ("32 px", 32)]
    pad, top, cap = 36, 74, 54
    width = pad + sum(s + pad for _, s in cols)
    sheet = Image.new("RGB", (width, top + 256 + cap), "#FFFFFF")
    d = ImageDraw.Draw(sheet)
    d.text((pad, 28), "Cloudy Canvas - chosen mark, transparent background",
           font=font(20, True), fill="#1B1B1F")
    x = pad
    for label, size in cols:
        y = top + (256 - size) // 2
        sheet.paste(checker(size), (x, y))
        im = img.resize((size, size), Image.LANCZOS)
        sheet.paste(im, (x, y), im)
        d.rectangle([x, y, x + size - 1, y + size - 1], outline="#CFCFD8")
        d.text((x, top + 256 + 12), label, font=font(15), fill="#5A5A66")
        x += size + pad
    out = os.path.join(OUT_DIR, "chosen-mark-transparent.png")
    sheet.save(out)
    return out


def main():
    rendered = {}
    for slug, fn in DESIGNS:
        for variant, pal in PALETTES.items():
            img = fn(pal)
            save_master(img, "%s-%s" % (slug, variant))
            rendered[(slug, variant)] = img.resize((S, S), Image.LANCZOS)
        print("done:", slug)
    print("sheet:", contact_sheet(rendered))

    chosen = rendered[(CHOSEN, "light")]
    icon = os.path.join("store-assets", "icon.png")
    chosen.resize((128, 128), Image.LANCZOS).save(icon)
    print("icon written:", icon)
    print("preview:", chosen_preview(chosen))


if __name__ == "__main__":
    main()
