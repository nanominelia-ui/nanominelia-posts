"""投稿画像(5枚)から BGM付き縦型リール(1080x1920 mp4)を生成する。
使い方: python tools/make_reel.py 31 [calm|warm] [出力先.mp4]
BGMは numpy で合成するオリジナル音源(著作権・ライセンスの問題なし)。"""
import sys, os, subprocess, wave, math
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance

W, H = 1080, 1920
DUR = [2.5, 3.5, 3.5, 3.5, 3.5]   # 表紙2.5秒、他3.5秒
FADE = 0.5                          # クロスフェード
FPS = 30

def total_len(): return sum(DUR) - FADE * (len(DUR) - 1)

def frame(src, out):
    s = Image.open(src).convert("RGB")
    bg = Image.new("RGB", (W, H))
    for y in range(H):
        t = y / H
        c = (int(34 + 30 * t), int(44 + 36 * t), int(88 + 40 * t))
        bg.paste(c, (0, y, W, y + 1))
    bg.paste(s, (0, (H - s.height) // 2))
    bg.save(out, quality=95)

CHORDS = {  # 各コード(Hz)。ゆったりした和音進行
    "calm": [[261.6, 329.6, 392.0, 493.9], [220.0, 261.6, 329.6, 392.0], [174.6, 220.0, 261.6, 329.6], [196.0, 246.9, 293.7, 392.0]],
    "warm": [[293.7, 370.0, 440.0, 554.4], [246.9, 293.7, 370.0, 440.0], [196.0, 246.9, 293.7, 370.0], [220.0, 277.2, 329.6, 440.0]],
}

def make_bgm(path, mood, seconds, sr=48000):
    n = int(seconds * sr); t = np.arange(n) / sr
    out = np.zeros(n)
    seg = seconds / 4
    for i, chord in enumerate(CHORDS[mood]):
        a, b = int(i * seg * sr), int(min((i + 1) * seg + 1.2, seconds) * sr)
        tt = np.arange(b - a) / sr
        env = np.minimum(tt / 0.9, 1) * np.minimum((tt.max() - tt) / 1.2, 1)
        for f in chord:
            for det, amp in ((0, 1.0), (0.6, 0.5), (-0.6, 0.5)):
                out[a:b] += amp * np.sin(2 * np.pi * (f + det) * tt) * env * 0.05
            out[a:b] += 0.015 * np.sin(2 * np.pi * f * 2 * tt) * env
    # やさしいアルペジオ
    for k in range(int(seconds / 0.9)):
        st = int(k * 0.9 * sr); chord = CHORDS[mood][min(int(k * 0.9 / seg), 3)]
        f = chord[k % 4] * 2; ln = int(0.8 * sr)
        if st + ln > n: break
        tt = np.arange(ln) / sr
        out[st:st + ln] += 0.05 * np.sin(2 * np.pi * f * tt) * np.exp(-3.2 * tt) * np.minimum(tt / 0.01, 1)
    # 擬似リバーブ
    for d, g in ((0.23, 0.35), (0.41, 0.25), (0.67, 0.18)):
        o = int(d * sr); out[o:] += g * out[:-o]
    out /= np.abs(out).max() + 1e-9
    stereo = np.stack([out, np.roll(out, int(0.012 * sr))], 1)
    pcm = (stereo * 0.8 * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())

def pick_bgm(no, mood, seconds, tmp):
    """bgm/ にある音源(例: calm_01.mp3, warm_02.mp3)から選んで、長さに合わせて切り出す。なければ合成BGM。"""
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bgm")
    files = sorted(f for f in (os.listdir(d) if os.path.isdir(d) else [])
                   if f.lower().endswith((".mp3", ".wav", ".m4a", ".ogg")) and f.lower().startswith(mood))
    if not files:
        files = sorted(f for f in (os.listdir(d) if os.path.isdir(d) else []) if f.lower().endswith((".mp3", ".wav", ".m4a", ".ogg")))
    out = f"{tmp}/bgm.wav"
    if not files:
        make_bgm(out, mood, seconds); return out
    src = os.path.join(d, files[no % len(files)])
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "0", "-i", src, "-t", f"{seconds:.2f}",
                    "-ar", "48000", "-ac", "2", out], check=True)
    return out

def build(no, mood="calm", out=None, root="public/posts", tmp="/tmp/reel"):
    os.makedirs(tmp, exist_ok=True)
    frames = []
    for i in range(1, 6):
        p = f"{tmp}/f{i}.jpg"; frame(f"{root}/{no:02d}/{i}.jpg", p); frames.append(p)
    L = total_len(); bgm = pick_bgm(no, mood, L, tmp)
    out = out or f"videos/reel_{no:02d}.mp4"; os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    for d, p in zip(DUR, frames): cmd += ["-loop", "1", "-t", str(d + FADE), "-i", p]
    cmd += ["-i", bgm]
    fc, last, off = [], "[0:v]", 0.0
    for i in range(1, 5):
        off += DUR[i - 1] - FADE
        fc.append(f"{last}[{i}:v]xfade=transition=fade:duration={FADE}:offset={off:.2f}[v{i}]"); last = f"[v{i}]"
    fc.append(f"{last}format=yuv420p,fps={FPS},trim=0:{L:.2f},setpts=PTS-STARTPTS[v]")
    fc.append(f"[5:a]loudnorm=I=-16:TP=-1.5:LRA=7,afade=t=out:st={L-1.5:.2f}:d=1.5,atrim=0:{L:.2f}[a]")
    cmd += ["-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-profile:v", "high", "-level", "4.0", "-pix_fmt", "yuv420p", "-r", str(FPS),
            "-b:v", "5M", "-maxrate", "6M", "-bufsize", "10M", "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2",
            "-movflags", "+faststart", "-t", f"{L:.2f}", out]
    subprocess.run(cmd, check=True); return out

if __name__ == "__main__":
    no = int(sys.argv[1]); mood = sys.argv[2] if len(sys.argv) > 2 else "calm"
    print(build(no, mood, sys.argv[3] if len(sys.argv) > 3 else None))
