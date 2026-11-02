# -*- coding: utf-8 -*-
"""
analyze_render.py — レンダしたPDFの頁数·頁サイズを集計し、目視確認用PNGを書き出す。
出力先は render_survey/ 配下のみ。
"""
import os
import glob
import json
import pymupdf

OUT = r"C:\Users\ss80751\kohden-code-workspace\20261102_管理文書用語と相関図\render_survey"
PNG_DIR = os.path.join(OUT, "png")
os.makedirs(PNG_DIR, exist_ok=True)

# PNG化する頁(1始まり)。None は 1〜3 頁目。
PICK = {
    ("Pana-CIM", "表紙"): [1],
    ("Pana-CIM", "目次"): [1, 2],
    ("Pana-CIM", "相関図"): [1],
    ("Pana-CIM", "相関図_old"): [1, 2],
    ("Pana-CIM", "月次再起動"): [1, 2, 3],
    ("Pana-CIM", "バックアップ"): [1, 2, 3],
    ("Pana-CIM", "復旧"): [1, 2],
    ("Pana-CIM", "異常時の対応"): [1, 2, 3],
    ("Pana-CIM", "会議課題一覧(一時)"): [1, 2, 3],
    ("Pana-CIM", "付録 引用元と確認範囲"): [1, 2],
    ("Pana-CIM", "7-5仮_サービス起動停止"): [1, 2],
    ("LNB", "構成と管理情報"): [1, 2, 3],
    ("LNB", "日次点検"): [1],
    ("LNB", "定期管理"): [1, 2],
    ("LNB", "チェックシート(日次)"): [1, 2],
    ("LNB", "引用と部品照合"): [1, 2],
    # 追加レンダ(全シート検証)
    ("Pana-CIM", "用語"): [1],
    ("Pana-CIM", "構成と管理情報"): [1, 2],
    ("Pana-CIM", "管理体制"): [1],
    ("Pana-CIM", "チェックシート(月次・異常時)"): [1, 2],
    ("Pana-CIM", "要確認事項一覧"): [1, 2],
    ("LNB", "表紙"): [1, 2],
    ("LNB", "目次"): [1, 2],
    ("LNB", "用語"): [1],
    ("LNB", "相関図"): [1],
    ("LNB", "相関図_old"): [1],
    ("LNB", "管理体制"): [1],
    ("LNB", "バックアップ"): [1, 2],
    ("LNB", "復旧"): [1],
    ("LNB", "異常時の対応"): [1, 2],
    ("LNB", "チェックシート(月次・異常時)"): [1, 2],
    ("LNB", "会議課題一覧(一時)"): [1, 2],
    ("LNB", "要確認事項一覧"): [1, 2],
}


def main() -> None:
    summary = []
    for book in ("Pana-CIM", "LNB"):
        for pdf_path in sorted(glob.glob(os.path.join(OUT, book, "*.pdf"))):
            sheet = os.path.splitext(os.path.basename(pdf_path))[0]
            doc = pymupdf.open(pdf_path)
            pages = []
            for i, page in enumerate(doc, start=1):
                r = page.rect
                pages.append(
                    {
                        "page": i,
                        "w_pt": round(r.width, 1),
                        "h_pt": round(r.height, 1),
                        "orientation": "L" if r.width > r.height else "P",
                    }
                )
            doc.close()
            summary.append(
                {
                    "book": book,
                    "sheet": sheet,
                    "pdf": pdf_path,
                    "page_count": len(pages),
                    "first3": pages[:3],
                    "orientations": "".join(p["orientation"] for p in pages),
                }
            )
            wanted = PICK.get((book, sheet), [])
            doc = pymupdf.open(pdf_path)
            for pno in wanted:
                if 1 <= pno <= doc.page_count:
                    page = doc[pno - 1]
                    pix = page.get_pixmap(dpi=100)
                    png_path = os.path.join(
                        PNG_DIR, f"{book}_{sheet}_p{pno:02d}.png"
                    )
                    pix.save(png_path)
            doc.close()

    out_path = os.path.join(OUT, "page_summary.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    for s in summary:
        print(
            f"{s['book']:<9} {s['sheet']:<22} {s['page_count']:>3}頁 "
            f"向き{s['orientations']}"
        )


if __name__ == "__main__":
    main()
