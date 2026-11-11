"""スライド全体のデザイン違い(5枚セット)を作る。
style=photo   : 写真を全面に敷いて白文字(全スライド写真)
style=minimal : クリーム地＋大きな藍色の文字(写真なし)
使い方(Actions): python tools/styles.py requests/style_samples.json  → samples/<no>_<style>/1..5.jpg"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont
sys.path.insert(0, os.path.dirname(__file__))
import photo_cover as pc

W, H = 1080, 1350
INDIGO = (43, 58, 103); PINK = (249, 168, 200); CREAM = (251, 247, 242); ACCENT = (214, 120, 160)
LABELS = ["", "ANSWER", "WHY", "POINT", "CTA"]
f = pc.font

def lines_for(d, text, size, maxw):
    fo = f(size); return fo, pc.wrap(text, d, fo, maxw)

def fit(d, text, maxw, maxlines, sizes):
    for s in sizes:
        fo, ls = lines_for(d, text, s, maxw)
        if len(ls) <= maxlines: return fo, ls, s
    return fo, ls, s

def header(d, no, i, color=(255, 255, 255), pill_fill=PINK, pill_txt=INDIGO):
    d.text((90, 92), "N A N O M I N E L I A", font=f(30), fill=color)
    t = f"{i} / 5"; d.text((W - 90 - d.textlength(t, font=f(28)), 96), t, font=f(28), fill=color)

def label(d, text, y, fill=PINK, txt=INDIGO):
    if not text: return
    fo = f(30); w = d.textlength(text, font=fo) + 56
    d.rounded_rectangle([90, y, 90 + w, y + 58], radius=29, fill=fill); d.text((90 + 28, y + 9), text, font=fo, fill=txt)

def photo_slide(no, i, text, photo, out):
    base = pc.cover_crop(photo)
    if i > 1: base = base.filter(ImageFilter.GaussianBlur(5))
    img = base.convert("RGBA")
    ov = Image.new("RGBA", (W, H)); px = ImageDraw.Draw(ov)
    for y in range(H):
        a = int(110 + 90 * (y / H)) if i > 1 else int(40 + 195 * (y / H) ** 1.7)
        px.line([(0, y), (W, y)], fill=INDIGO + (min(a, 235),))
    img = Image.alpha_composite(img, ov); d = ImageDraw.Draw(img)
    if i == 1:
        pc.make(no, text, photo, out); return
    header(d, no, i); label(d, LABELS[i - 1], 330)
    fo, ls, s = fit(d, text, W - 180, 6, (66, 60, 54, 48))
    y = max(440, int((H - len(ls) * s * 1.5) / 2) + 20)
    for ln in ls: d.text((90, y), ln, font=fo, fill=(255, 255, 255)); y += int(s * 1.5)
    d.rounded_rectangle([90, y + 20, 210, y + 26], radius=3, fill=PINK)
    os.makedirs(os.path.dirname(out), exist_ok=True); img.convert("RGB").save(out, "JPEG", quality=92, subsampling=0)

def minimal_slide(no, i, text, out):
    img = Image.new("RGB", (W, H), CREAM); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 18, H], fill=INDIGO)
    header(d, no, i, color=INDIGO)
    d.text((W - 90 - d.textlength(f"{i:02d}", font=f(300)), 150), f"{i:02d}", font=f(300), fill=(238, 230, 238))
    if i == 1:
        fo, ls, s = fit(d, text, W - 200, 4, (96, 88, 80, 72))
        y = 520; d.rounded_rectangle([100, y - 50, 220, y - 42], radius=4, fill=ACCENT)
        for ln in ls: d.text((100, y), ln, font=fo, fill=INDIGO); y += int(s * 1.5)
        d.text((100, 1180), f"VOL.{no}   SWIPE  >>>", font=f(32), fill=ACCENT)
    else:
        label(d, LABELS[i - 1], 360, fill=INDIGO, txt=(255, 255, 255))
        fo, ls, s = fit(d, text, W - 200, 6, (64, 58, 52, 46))
        y = max(470, int((H - len(ls) * s * 1.5) / 2) + 20)
        for ln in ls: d.text((100, y), ln, font=fo, fill=INDIGO); y += int(s * 1.5)
        d.rounded_rectangle([100, y + 24, 220, y + 30], radius=3, fill=ACCENT)
    os.makedirs(os.path.dirname(out), exist_ok=True); img.save(out, "JPEG", quality=92, subsampling=0)


YELLOW = (255, 214, 92); MAGENTA = (190, 70, 150)

def _grad(c1, c2, diag=True):
    img = Image.new("RGB", (W, H)); px = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H; px.line([(0, y), (W, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(c1, c2)))
    return img

def _draw_marked(d, ls, fo, s, x, y, em, hl, color, center=False):
    """行ごとに描画。emに一致する語の背後にマーカー(蛍光色の帯)を引く。"""
    for ln in ls:
        lx = (W - d.textlength(ln, font=fo)) / 2 if center else x
        if em and em in ln:
            a = ln.index(em); x0 = lx + d.textlength(ln[:a], font=fo); x1 = x0 + d.textlength(em, font=fo)
            d.rectangle([x0 - 8, y + s * 0.74, x1 + 8, y + s * 1.14], fill=hl)
        d.text((lx, y), ln, font=fo, fill=color); y += int(s * 1.45)
    return y

def bold_slide(no, i, text, out, stat=None, em=None):
    bgs = {1: _grad((38, 40, 110), MAGENTA), 2: YELLOW, 3: PINK, 4: INDIGO, 5: _grad(MAGENTA, (38, 40, 110))}
    bg = bgs[i]; img = bg.copy() if isinstance(bg, Image.Image) else Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img, "RGBA")
    dark = i in (1, 4, 5); fg = (255, 255, 255) if dark else INDIGO
    hl = YELLOW if dark else (255, 255, 255)
    # 飾り: 大きな円と斜めの帯
    d.ellipse([W - 380, -200, W + 160, 340], fill=(255, 255, 255, 38 if dark else 60))
    d.ellipse([-220, H - 360, 360, H + 200], fill=(255, 255, 255, 30 if dark else 55))
    d.polygon([(0, H - 150), (W, H - 300), (W, H - 250), (0, H - 100)], fill=(YELLOW if i != 2 else INDIGO) + (255,)) if i in (1, 5) else None
    d.text((70, 80), "N A N O M I N E L I A", font=f(30), fill=fg)
    d.text((W - 70 - d.textlength(f"{i}/5", font=f(30)), 80), f"{i}/5", font=f(30), fill=fg)
    if i == 1:
        fo, ls, s = fit(d, text, W - 140, 4, (128, 116, 104, 92, 80))
        y = 300 if stat is None else 520
        if stat:
            fs = f(210); tw = d.textlength(stat, font=fs)
            d.text(((W - tw) / 2, 230), stat, font=fs, fill=YELLOW)
        y = _draw_marked(d, ls, fo, s, 70, y + (0 if stat else 120), em, (255, 90, 150), fg, center=True)
        sw = d.textlength("SWIPE  >>>", font=f(34)) + 70
        d.rounded_rectangle([(W - sw) / 2, 1190, (W + sw) / 2, 1262], radius=36, fill=INDIGO)
        d.text(((W - sw) / 2 + 35, 1203), "SWIPE  >>>", font=f(34), fill=(255, 255, 255))
    else:
        tag = LABELS[i - 1]; fo = f(36); tw = d.textlength(tag, font=fo) + 70
        d.rounded_rectangle([70, 230, 70 + tw, 306], radius=38, fill=(INDIGO if not dark else YELLOW))
        d.text((70 + 35, 243), tag, font=fo, fill=((255, 255, 255) if not dark else INDIGO))
        d.text((W - 70 - d.textlength(str(i - 1), font=f(190)), 140), str(i - 1), font=f(190), fill=(255, 255, 255, 45 if dark else 70))
        top = 400
        if stat and i == 2:
            fs = f(190); d.text((70, 360), stat, font=fs, fill=INDIGO); top = 620
        fo, ls, s = fit(d, text, W - 140, 7, (76, 70, 64, 56, 50))
        n = len(ls); top = max(top, int((H - n * s * 1.45) / 2)) if not (stat and i == 2) else top
        _draw_marked(d, ls, fo, s, 70, top, em if i == 2 else None, hl, fg)
    os.makedirs(os.path.dirname(out), exist_ok=True); img.convert("RGB").save(out, "JPEG", quality=92, subsampling=0)

SERIF = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
GOLD = (176, 140, 78); IVORY = (248, 244, 237); NAVY = (28, 38, 74)
def sf(size):
    try: return ImageFont.truetype(SERIF, size, index=0)
    except Exception: return pc.font(size)

def _rr_photo(img, photo, box, radius=28):
    x0, y0, x1, y1 = box; w, h = x1 - x0, y1 - y0
    r = max(w / photo.width, h / photo.height)
    p = photo.resize((int(photo.width * r) + 1, int(photo.height * r) + 1), Image.LANCZOS)
    p = p.crop(((p.width - w) // 2, (p.height - h) // 2, (p.width - w) // 2 + w, (p.height - h) // 2 + h))
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w, h], radius=radius, fill=255)
    img.paste(p, (x0, y0), m)

def editorial_slide(no, i, text, out, photo=None):
    img = Image.new("RGB", (W, H), IVORY); d = ImageDraw.Draw(img)
    d.text((80, 70), "NANOMINELIA", font=sf(28), fill=GOLD)
    t = f"{i} / 5"; d.text((W - 80 - d.textlength(t, font=sf(28)), 70), t, font=sf(28), fill=GOLD)
    d.line([(80, 124), (W - 80, 124)], fill=GOLD, width=2)
    if i == 1:
        if photo is not None: _rr_photo(img, photo, (80, 170, W - 80, 800))
        d.text((80, 840), f"MINERAL NOTES  No.{no}", font=sf(28), fill=GOLD)
        fo, ls, s = fit(d, text, W - 160, 3, (80, 72, 64, 56))
        y = 880
        for ln in ls: d.text((80, y), ln, font=fo, fill=NAVY); y += int(s * 1.45)
        d.line([(80, y + 20), (260, y + 20)], fill=GOLD, width=4)
        d.text((80, 1262), "SWIPE  →", font=sf(30), fill=GOLD)
    else:
        d.text((80, 250), f"{i - 1:02d}", font=sf(170), fill=(228, 214, 186))
        d.text((80, 470), LABELS[i - 1], font=sf(30), fill=GOLD); d.line([(80, 520), (200, 520)], fill=GOLD, width=3)
        fo, ls, s = fit(d, text, W - 170, 7, (62, 56, 52, 46))
        y = max(580, int((H - len(ls) * s * 1.7) / 2) + 80)
        d.rectangle([80, y, 86, y + int(len(ls) * s * 1.7) - 20], fill=GOLD)
        for ln in ls: d.text((120, y), ln, font=fo, fill=NAVY); y += int(s * 1.7)
    os.makedirs(os.path.dirname(out), exist_ok=True); img.save(out, "JPEG", quality=92, subsampling=0)

def _spaced(d, xy, text, font, fill, gap=10, anchor="l"):
    x, y = xy; tw = sum(d.textlength(c, font=font) + gap for c in text) - gap
    if anchor == "c": x = x - tw / 2
    for c in text:
        d.text((x, y), c, font=font, fill=fill); x += d.textlength(c, font=font) + gap
    return tw

def _shade(img, top, bottom, y0=0, y1=H):
    ov = Image.new("RGBA", (W, H)); px = ImageDraw.Draw(ov)
    for y in range(y0, y1):
        t = (y - y0) / max(1, y1 - y0); a = int(top + (bottom - top) * t)
        px.line([(0, y), (W, y)], fill=(10, 14, 36, max(0, min(255, a))))
    return Image.alpha_composite(img.convert("RGBA"), ov)

def magazine_slide(no, i, text, out, photo, kicker="MINERAL NOTES", stat=None, em=None):
    base = pc.cover_crop(photo)
    if i == 1:
        img = _shade(base, 175, 0, 0, 440)              # 上部(題字用)を少し暗く
        img = Image.alpha_composite(img, _shade(base, 0, 0)) if False else img
        ov2 = _shade(base.convert("RGB"), 0, 205, 620, H); img = Image.alpha_composite(img, ov2) if False else Image.blend(img, ov2, 0.0) if False else img
        # 下部グラデーションを別途合成
        bt = Image.new("RGBA", (W, H)); px = ImageDraw.Draw(bt)
        for y in range(560, H): px.line([(0, y), (W, y)], fill=(10, 14, 36, int(215 * ((y - 560) / (H - 560)) ** 1.3)))
        img = Image.alpha_composite(img, bt); d = ImageDraw.Draw(img)
        mast = sf(150); tw = d.textlength("NANOMINELIA", font=mast)
        size = 150
        while tw > W - 120 and size > 80: size -= 4; mast = sf(size); tw = d.textlength("NANOMINELIA", font=mast)
        d.text(((W - tw) / 2, 70), "NANOMINELIA", font=mast, fill=(255, 255, 255))
        d.line([(60, 70 + size + 28), (W - 60, 70 + size + 28)], fill=(255, 255, 255), width=3)
        _spaced(d, (60, 70 + size + 44), f"ISSUE {no}", sf(26), (255, 255, 255), 6)
        _spaced(d, (W - 60, 70 + size + 44), kicker, sf(26), (255, 255, 255), 6, anchor="l") if False else None
        kw = sum(d.textlength(c, font=sf(26)) + 6 for c in kicker) - 6
        _spaced(d, (W - 60 - kw, 70 + size + 44), kicker, sf(26), (255, 255, 255), 6)
        # スタッツ or NEW のバッジ
        badge = stat or "NEW"; bf = sf(70 if len(badge) <= 4 else 54)
        cx, cy, r = 880, 560, 120
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 214, 92)); d.ellipse([cx - r + 10, cy - r + 10, cx + r - 10, cy + r - 10], outline=INDIGO, width=3)
        bw = d.textlength(badge, font=bf); d.text((cx - bw / 2, cy - 70), badge, font=bf, fill=INDIGO)
        sw = d.textlength("TODAY", font=sf(24)); d.text((cx - sw / 2, cy + 38), "TODAY", font=sf(24), fill=INDIGO)
        nl = text.count("\n") + 1
        for sz in (118, 106, 96, 86, 76, 68):
            fo = sf(sz) if False else f(sz); ls = pc.wrap(text, d, fo, W - 160); s_ = sz
            if len(ls) <= nl: break
        y = H - 190 - int(len(ls) * s_ * 1.3)
        for ln in ls:
            d.text((62, y + 3), ln, font=fo, fill=(0, 0, 0, 90)); d.text((60, y), ln, font=fo, fill=(255, 255, 255)); y += int(s_ * 1.3)
        d.rectangle([60, y + 14, 200, y + 20], fill=(255, 214, 92))
        _spaced(d, (60, H - 96), "SWIPE  →", sf(30), (255, 255, 255), 6)
        bx = W - 60 - 190                                   # バーコード風
        d.rectangle([bx, H - 120, W - 60, H - 50], fill=(255, 255, 255))
        import random as _r; rr = _r.Random(no); x = bx + 10
        while x < W - 70: w = rr.choice((2, 3, 5)); d.rectangle([x, H - 112, x + w, H - 58], fill=(20, 20, 40)); x += w + rr.choice((3, 4, 6))
    else:
        img = Image.new("RGB", (W, H), IVORY); d = ImageDraw.Draw(img)
        ph = 700
        r_ = max(W / base.width, ph / base.height) if False else None
        ph_img = pc.cover_crop(photo).crop((0, 0, W, ph)) if i % 2 == 0 else pc.cover_crop(photo).crop((0, H - ph, W, H))
        sh = Image.new("RGBA", (W, ph)); sp = ImageDraw.Draw(sh)
        for yy in range(260): sp.line([(0, yy), (W, yy)], fill=(10, 14, 36, int(150 * (1 - yy / 260))))
        ph_img = Image.alpha_composite(ph_img.convert("RGBA"), sh).convert("RGB")
        img.paste(ph_img, (0, 0)); d = ImageDraw.Draw(img)
        d.text((60, 52), "NANOMINELIA", font=sf(34), fill=(255, 255, 255))
        pn = f"P.{i:02d}"; d.text((W - 60 - d.textlength(pn, font=sf(34)), 52), pn, font=sf(34), fill=(255, 255, 255))
        d.text((50, ph - 300), f"{i - 1:02d}", font=sf(240), fill=(255, 255, 255))
        d.rectangle([0, ph, W, ph + 10], fill=(255, 214, 92))
        _spaced(d, (60, ph + 56), LABELS[i - 1], sf(32), GOLD, 10)
        fo, ls, s_ = fit(d, text, W - 120, 4, (64, 58, 52, 46))
        y = ph + 120
        for ln in ls: d.text((60, y), ln, font=fo, fill=NAVY); y += int(s_ * 1.5)
        d.line([(60, H - 80), (W - 60, H - 80)], fill=GOLD, width=2)
        _spaced(d, (60, H - 62), f"ISSUE {no}  /  {kicker}", sf(22), GOLD, 5)
        img = img.convert("RGBA")
    os.makedirs(os.path.dirname(out), exist_ok=True); img.convert("RGB").save(out, "JPEG", quality=92, subsampling=0)

def build(r, photos=None):
    texts = [r["hook"].replace("\\n", "\n"), r["ans"], r["why"], r["pt"], r["cta"]]
    outs = {}
    for style in r.get("styles", ["photo", "minimal"]):
        for i, t in enumerate(texts, 1):
            out = f"public/posts/{r['no']:02d}/{i}.jpg" if r.get("apply") else f"samples/{r['no']}_{style}/{i}.jpg"
            if style == "photo": photo_slide(r["no"], i, t, photos[(i - 1) % len(photos)], out)
            elif style == "magazine": magazine_slide(r["no"], i, t, out, photos[(i - 1) % len(photos)], r.get("kicker", "MINERAL NOTES"), r.get("stat"), r.get("em"))
            elif style == "editorial": editorial_slide(r["no"], i, t, out, photos[0] if photos else None)
            elif style == "bold": bold_slide(r["no"], i, t, out, r.get("stat"), r.get("em"))
            else: minimal_slide(r["no"], i, t, out)
    return outs

if __name__ == "__main__":
    for r in json.load(open(sys.argv[1])):
        photos = []
        if any(x in r.get("styles", ["photo", "minimal"]) for x in ("photo", "editorial", "magazine")):
            for k, q in enumerate(r["queries"]):
                p, src = pc.fetch_photo(q, r["no"] * 10 + k); photos.append(p); print("photo", q, src)
        build(r, photos); print("ok", r["no"])
