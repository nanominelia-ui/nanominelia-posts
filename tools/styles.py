"""スライド全体のデザイン違い(5枚セット)を作る。
style=photo   : 写真を全面に敷いて白文字(全スライド写真)
style=minimal : クリーム地＋大きな藍色の文字(写真なし)
使い方(Actions): python tools/styles.py requests/style_samples.json  → samples/<no>_<style>/1..5.jpg"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFilter
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

def build(r, photos=None):
    texts = [r["hook"].replace("\\n", "\n"), r["ans"], r["why"], r["pt"], r["cta"]]
    outs = {}
    for style in r.get("styles", ["photo", "minimal"]):
        for i, t in enumerate(texts, 1):
            out = f"samples/{r['no']}_{style}/{i}.jpg"
            if style == "photo": photo_slide(r["no"], i, t, photos[(i - 1) % len(photos)], out)
            elif style == "bold": bold_slide(r["no"], i, t, out, r.get("stat"), r.get("em"))
            else: minimal_slide(r["no"], i, t, out)
    return outs

if __name__ == "__main__":
    for r in json.load(open(sys.argv[1])):
        photos = []
        if "photo" in r.get("styles", ["photo", "minimal"]):
            for k, q in enumerate(r["queries"]):
                p, src = pc.fetch_photo(q, r["no"] * 10 + k); photos.append(p); print("photo", q, src)
        build(r, photos); print("ok", r["no"])
