"""リール動画の一括生成と、古い動画の自動削除。
- public/posts/NN/ に画像5枚がそろっていて、まだ動画にしていない投稿(NN >= START)を、public/videos/reel_NN.mp4 に生成
- 最後のコミットから KEEP_DAYS 日より古い動画は削除(index.json は残すので、作り直しはしない)"""
import os, sys, json, glob, subprocess, time
sys.path.insert(0, os.path.dirname(__file__))
import make_reel

START, KEEP_DAYS, MAX_BUILD = 31, 7, 12
VID = "public/videos"; IDX = f"{VID}/index.json"

def main():
    os.makedirs(VID, exist_ok=True)
    idx = json.load(open(IDX)) if os.path.exists(IDX) else {"built": []}
    built = set(idx["built"]); n = 0
    for d in sorted(glob.glob("public/posts/[0-9][0-9]")):
        no = int(os.path.basename(d))
        if no < START or no in built: continue
        if not all(os.path.exists(f"{d}/{i}.jpg") for i in range(1, 6)): continue
        if n >= MAX_BUILD: break
        make_reel.build(no, "calm" if no % 2 else "warm", f"{VID}/reel_{no:02d}.mp4"); built.add(no); n += 1
        print("built", no)
    idx["built"] = sorted(built); json.dump(idx, open(IDX, "w"))
    now = time.time()
    for f in glob.glob(f"{VID}/reel_*.mp4"):
        ts = subprocess.run(["git", "log", "-1", "--format=%ct", "--", f], capture_output=True, text=True).stdout.strip()
        if ts and now - int(ts) > KEEP_DAYS * 86400: os.remove(f); print("deleted old", f)

if __name__ == "__main__": main()
# trigger
