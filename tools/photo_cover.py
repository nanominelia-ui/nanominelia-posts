"""写真つき表紙(1.jpg)を自動生成: Pexels APIで写真取得 → 藍色グラデーション＋文字を合成。
requests/photo_cover.json の各エントリ {no, query, hook} を処理し、public/posts/NN/1.jpg を上書きする。
環境変数 PEXELS_API_KEY が必要。"""
import json, os, sys, io, urllib.request, urllib.parse, random
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
INDIGO = (43, 58, 103); PINK = (249, 168, 200)
NO_START = set("。、，．！？!?）)」』】…ー〜～・：:;”’")

def font(size): return ImageFont.truetype(BOLD, size, index=0)

def _get(url, headers=None):
    return urllib.request.urlopen(urllib.request.Request(url, headers=headers or {"User-Agent": "nanominelia-bot"}), timeout=60).read()

def fetch_photo(query, seed):
    """PIXABAY_API_KEY があれば Pixabay、なければ PEXELS_API_KEY で Pexels から取得。"""
    pk = os.environ.get("PIXABAY_API_KEY", "").strip()
    if pk:
        url = "https://pixabay.com/api/?" + urllib.parse.urlencode({
            "key": pk, "q": query, "image_type": "photo", "orientation": "vertical",
            "min_width": 800, "min_height": 1000, "safesearch": "true", "per_page": 50})
        hits = json.loads(_get(url)).get("hits", [])
        PEOPLE = {"man", "woman", "girl", "boy", "child", "children", "baby", "people", "person", "face", "portrait",
                  "model", "lady", "male", "female", "kid", "couple", "family", "hand", "hands", "logo", "brand", "text", "sign"}
        words = [w.lower() for w in query.replace(",", " ").split()]
        def tagset(h): return {t.strip().lower() for t in h.get("tags", "").replace(",", " ").split()}
        ok = [h for h in hits if not (tagset(h) & PEOPLE)]
        # 検索語がタグに多く含まれる写真を優先(内容との一致)
        ok.sort(key=lambda h: -sum(1 for w in words if w in tagset(h) or any(w in t for t in tagset(h))))
        if not ok: raise SystemExit(f"no photo for {query}")
        h = random.Random(seed).choice(ok[:4])
        print("  pick:", h.get("tags"))
        return Image.open(io.BytesIO(_get(h["largeImageURL"]))).convert("RGB"), h.get("pageURL", "")
    key = os.environ["PEXELS_API_KEY"].strip()
    url = "https://api.pexels.com/v1/search?" + urllib.parse.urlencode(
        {"query": query, "orientation": "portrait", "per_page": 15, "size": "large"})
    photos = json.loads(_get(url, {"Authorization": key, "User-Agent": "nanominelia-bot"})).get("photos", [])
    if not photos: raise SystemExit(f"no photo for {query}")
    p = random.Random(seed).choice(photos[:8])
    return Image.open(io.BytesIO(_get(p["src"].get("large2x") or p["src"]["large"]))).convert("RGB"), p.get("url", "")

def cover_crop(img):
    r = max(W / img.width, H / img.height)
    img = img.resize((int(img.width * r) + 1, int(img.height * r) + 1), Image.LANCZOS)
    x, y = (img.width - W) // 2, (img.height - H) // 2
    return img.crop((x, y, x + W, y + H))

def wrap(text, d, f, maxw):
    lines = []
    for para in text.split("\n"):
        cur = ""
        for ch in para:
            if d.textlength(cur + ch, font=f) > maxw and cur and ch not in NO_START:
                lines.append(cur); cur = ch
            else: cur += ch
        lines.append(cur)
    return lines

def make(no, hook, photo, out):
    img = cover_crop(photo).convert("RGBA")
    ov = Image.new("RGBA", (W, H))
    px = ImageDraw.Draw(ov)
    for y in range(H):  # 下ほど濃い藍色(文字の可読性)
        a = int(40 + 195 * (y / H) ** 1.7)
        px.line([(0, y), (W, y)], fill=INDIGO + (min(a, 235),))
    img = Image.alpha_composite(img, ov)
    d = ImageDraw.Draw(img)
    d.text((90, 92), "N A N O M I N E L I A", font=font(30), fill=(255, 255, 255))
    pill = f"VOL.{no}"; fp = font(26); pw = d.textlength(pill, font=fp) + 44
    d.rounded_rectangle([W - 90 - pw, 74, W - 90, 126], radius=26, fill=PINK)
    d.text((W - 90 - pw + 22, 84), pill, font=fp, fill=INDIGO)
    for size in (88, 80, 72, 64, 56):
        f = font(size); lines = wrap(hook, d, f, W - 180); lh = int(size * 1.35)
        if len(lines) <= 3: break
    y = 1010 - len(lines) * lh // 2 - 40 + 60
    for ln in lines:
        d.text(((W - d.textlength(ln, font=f)) / 2, y), ln, font=f, fill=(255, 255, 255)); y += lh
    d.rounded_rectangle([450, y + 8, 630, y + 14], radius=3, fill=PINK)
    fs = font(30); label = "SWIPE  >>>"; lw = d.textlength(label, font=fs) + 60
    d.rounded_rectangle([(W - lw) / 2, 1236, (W + lw) / 2, 1296], radius=30, fill=PINK)
    d.text(((W - lw) / 2 + 30, 1246), label, font=fs, fill=INDIGO)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img.convert("RGB").save(out, "JPEG", quality=92, subsampling=0)

if __name__ == "__main__":
    reqs = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "requests/photo_cover.json"))
    for r in reqs:
        photo, src = fetch_photo(r["query"], r["no"])
        make(r["no"], r["hook"].replace("\\n", "\n"), photo, f"public/posts/{r['no']:02d}/1.jpg")
        print("ok", r["no"], r["query"], src)
