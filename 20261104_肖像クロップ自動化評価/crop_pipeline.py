# -*- coding: utf-8 -*-
"""J-02 肖像クロップ自動化 実現可能性評価パイプライン.

testdata/ の全PNGを対象に、顔検出(Haar→アニメ顔LBP)→主顔選択→
3:4クロップ→600x800 JPEG出力を行い、mapping.csv と contact_sheet.html を
作成して集計を標準出力に表示する。

実行: python -X utf8 crop_pipeline.py
"""
import csv
import shutil
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import cv2
import numpy as np

# ---- 設定定数 ----
BASE_DIR = Path(__file__).resolve().parent
TESTDATA_DIR = BASE_DIR / "testdata"
SAMPLES_DIR = BASE_DIR / "samples"
MODELS_DIR = BASE_DIR / "models"
ANIMEFACE_URL = (
    "https://raw.githubusercontent.com/nagadomi/lbpcascade_animeface/"
    "master/lbpcascade_animeface.xml"
)
ANIMEFACE_PATH = MODELS_DIR / "lbpcascade_animeface.xml"

MARGIN_LR = 0.60       # 左右の余白(顔幅に対する割合)
MARGIN_TOP = 0.45      # 上の余白(顔高に対する割合)
MARGIN_BOTTOM = 0.90   # 下の余白(顔高に対する割合)
ASPECT_W, ASPECT_H = 3, 4   # 出力縦横比(幅:高さ)
OUT_W, OUT_H = 600, 800     # 出力サイズ
JPEG_QUALITY = 90

# ---- 画像入出力(日本語パス対応) ----

def imread_unicode(path: Path):
    data = np.fromfile(str(path), dtype=np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def imwrite_jpeg_unicode(path: Path, img, quality: int) -> bool:
    ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not ok:
        return False
    buf.tofile(str(path))
    return True


# ---- 検出器の準備 ----

def ensure_animeface_cascade() -> str:
    """アニメ顔カスケードを確保する。パスを返す。確保できなければ空文字。"""
    if ANIMEFACE_PATH.exists() and ANIMEFACE_PATH.stat().st_size > 0:
        return str(ANIMEFACE_PATH)
    MODELS_DIR.mkdir(exist_ok=True)
    try:
        urllib.request.urlretrieve(ANIMEFACE_URL, ANIMEFACE_PATH)
        print(f"[info] lbpcascade_animeface.xml をダウンロードしました: {ANIMEFACE_PATH}")
        return str(ANIMEFACE_PATH)
    except Exception as e:
        print(f"[warn] lbpcascade_animeface.xml のダウンロードに失敗、アニメ顔検出器は使用しません: {e}")
        return ""


def load_cascades():
    haar = None
    try:
        haar_path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
        haar = cv2.CascadeClassifier(str(haar_path))
        if haar.empty():
            print(f"[warn] Haar cascade の読み込みに失敗: {haar_path}")
            haar = None
    except Exception as e:
        print(f"[warn] Haar cascade を初期化できません: {e}")
        haar = None

    anime = None
    anime_path = ensure_animeface_cascade()
    if anime_path:
        # OpenCV の FileStorage は Windows で日本語パスを開けないため、
        # ASCII 名の temp ファイルにコピーしてから読み込む
        load_path = anime_path
        try:
            anime_path.encode("ascii")
        except UnicodeEncodeError:
            tmp = Path(tempfile.gettempdir()) / "lbpcascade_animeface.xml"
            shutil.copyfile(anime_path, tmp)
            load_path = str(tmp)
        anime = cv2.CascadeClassifier(load_path)
        if anime.empty():
            print(f"[warn] アニメ顔カスケードの読み込みに失敗: {anime_path}")
            anime = None
    return haar, anime


def detect_faces(gray, cascade) -> list:
    if cascade is None:
        return []
    faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    if faces is None:
        return []
    return [tuple(int(v) for v in f) for f in faces]


# ---- クロップ計算 ----

def compute_crop(face, img_w: int, img_h: int):
    """主顔ボックスから 3:4 クロップ領域を求める。返値は int の (x, y, w, h)。"""
    fx, fy, fw, fh = face
    x = fx - fw * MARGIN_LR
    y = fy - fh * MARGIN_TOP
    w = fw * (1.0 + 2.0 * MARGIN_LR)
    h = fh * (1.0 + MARGIN_TOP + MARGIN_BOTTOM)

    # 3:4 に合わせて短い辺を広げる
    if w / h < ASPECT_W / ASPECT_H:
        new_w = h * ASPECT_W / ASPECT_H
        x -= (new_w - w) / 2.0
        w = new_w
    else:
        new_h = w * ASPECT_H / ASPECT_W
        y -= (new_h - h) / 2.0
        h = new_h

    # 画像の範囲内にクランプ
    w = min(w, float(img_w))
    h = min(h, float(img_h))
    x = min(max(x, 0.0), float(img_w - w))
    y = min(max(y, 0.0), float(img_h - h))
    return int(round(x)), int(round(y)), max(int(round(w)), 1), max(int(round(h)), 1)


# ---- 主処理 ----

def main() -> int:
    SAMPLES_DIR.mkdir(exist_ok=True)
    haar, anime = load_cascades()
    print(
        "[info] 検出器の状態: "
        f"haar={'利用可' if haar else '利用不可'} / animeface={'利用可' if anime else '利用不可'}"
    )

    images = sorted(p for p in TESTDATA_DIR.iterdir() if p.suffix.lower() == ".png")
    if not images:
        print("[error] testdata/ にPNGがありません")
        return 1

    rows = []
    per_image_times = []
    for src in images:
        person = src.stem
        t0 = time.perf_counter()
        img = imread_unicode(src)
        if img is None:
            per_image_times.append(time.perf_counter() - t0)
            rows.append({
                "source_file": src.name, "person_name": person, "detector": "none",
                "faces_found": 0, "chosen_face_box": "", "crop_box": "",
                "output_file": "", "status": "need_manual",
            })
            print(f"[ng] {src.name}: 読み込み失敗")
            continue
        img_h, img_w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        detector_used = "none"
        faces = detect_faces(gray, haar)
        if faces:
            detector_used = "haar"
        else:
            faces = detect_faces(gray, anime)
            if faces:
                detector_used = "animeface"

        faces_found = len(faces)
        elapsed = time.perf_counter() - t0
        per_image_times.append(elapsed)

        if faces_found == 0:
            rows.append({
                "source_file": src.name, "person_name": person, "detector": "none",
                "faces_found": 0, "chosen_face_box": "", "crop_box": "",
                "output_file": "", "status": "need_manual",
            })
            print(f"[need_manual] {src.name}: 顔検出0件 ({elapsed:.3f}s)")
            continue

        chosen = max(faces, key=lambda f: f[2] * f[3])
        cx, cy, cw, ch = compute_crop(chosen, img_w, img_h)
        crop = img[cy:cy + ch, cx:cx + cw]
        resized = cv2.resize(crop, (OUT_W, OUT_H), interpolation=cv2.INTER_AREA)
        out_name = f"{person}_3x4.jpg"
        out_path = SAMPLES_DIR / out_name
        saved = imwrite_jpeg_unicode(out_path, resized, JPEG_QUALITY)
        elapsed = time.perf_counter() - t0
        per_image_times[-1] = elapsed

        if not saved:
            rows.append({
                "source_file": src.name, "person_name": person, "detector": detector_used,
                "faces_found": faces_found, "chosen_face_box": f"{chosen[0]},{chosen[1]},{chosen[2]},{chosen[3]}",
                "crop_box": f"{cx},{cy},{cw},{ch}", "output_file": "", "status": "need_manual",
            })
            print(f"[ng] {src.name}: JPEG保存失敗 ({elapsed:.3f}s)")
            continue

        rows.append({
            "source_file": src.name, "person_name": person, "detector": detector_used,
            "faces_found": faces_found,
            "chosen_face_box": f"{chosen[0]},{chosen[1]},{chosen[2]},{chosen[3]}",
            "crop_box": f"{cx},{cy},{cw},{ch}",
            "output_file": f"samples/{out_name}", "status": "ok",
        })
        print(f"[ok] {src.name}: detector={detector_used} faces={faces_found} ({elapsed:.3f}s)")

    # mapping.csv (UTF-8 with BOM)
    csv_path = BASE_DIR / "mapping.csv"
    fieldnames = ["source_file", "person_name", "detector", "faces_found",
                  "chosen_face_box", "crop_box", "output_file", "status"]
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"[info] mapping.csv を出力: {csv_path}")

    # contact_sheet.html
    html_path = BASE_DIR / "contact_sheet.html"
    cells = []
    for r in rows:
        img_tag = (
            f'<img src="{r["output_file"]}" alt="{r["person_name"]}">'
            if r["output_file"] else '<div class="noimg">出力なし</div>'
        )
        cells.append(
            f'<div class="cell">{img_tag}'
            f'<div class="meta"><b>{r["person_name"]}</b><br>'
            f'detector: {r["detector"]} / faces: {r["faces_found"]}<br>'
            f'status: {r["status"]}</div></div>'
        )
    html = (
        '<!DOCTYPE html><html lang="ja"><head><meta charset="utf-8">'
        "<title>contact sheet - 肖像クロップ自動化評価</title><style>"
        "body{font-family:sans-serif;background:#222;color:#eee;}"
        ".grid{display:flex;flex-wrap:wrap;gap:16px;padding:16px;}"
        ".cell{width:220px;background:#333;border-radius:6px;padding:8px;}"
        ".cell img{width:100%;height:auto;display:block;}"
        ".noimg{height:280px;display:flex;align-items:center;justify-content:center;"
        "background:#555;color:#ddd;font-size:13px;}"
        ".meta{font-size:12px;margin-top:6px;line-height:1.5;}"
        "</style></head><body><h1>肖像クロップ自動化評価 contact sheet</h1>"
        f'<div class="grid">{"".join(cells)}</div></body></html>'
    )
    html_path.write_text(html, encoding="utf-8")
    print(f"[info] contact_sheet.html を出力: {html_path}")

    # 集計
    total = len(rows)
    ok_rows = [r for r in rows if r["status"] == "ok"]
    ok_count = len(ok_rows)
    ok_rate = ok_count / total * 100 if total else 0.0
    breakdown = {}
    for r in rows:
        key = r["detector"] if r["status"] == "ok" else "none"
        breakdown[key] = breakdown.get(key, 0) + 1

    print("\n===== 集計 =====")
    print(f"全体件数: {total}")
    print(f"ok件数: {ok_count} (率 {ok_rate:.1f}%)")
    print(f"検出器別内訳: {breakdown}")
    if per_image_times:
        print(f"1枚あたり平均処理時間: {sum(per_image_times) / len(per_image_times):.3f} 秒")
    return 0


if __name__ == "__main__":
    sys.exit(main())
