# -*- coding: utf-8 -*-
"""
render_survey_rest.py — 評価報告書の「推定」を実測に置き換えるため、
初回レンダで未実施だった17シートを追加でPDF化する。
- Excel COM: 読み取り専用で開く / 保存しない
- 出力先: render_survey/ 配下のみ
- 「申し送り(認証情報)」は認証情報を含むためレンダ対象から除外(内容も出力も不読)
"""
import os
import sys
import json
import win32com.client as win32

VAULT = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物"
OUT = r"C:\Users\ss80751\kohden-code-workspace\20261102_管理文書用語と相関図\render_survey"

BOOKS = {
    "Pana-CIM": {
        "path": os.path.join(VAULT, "Pana-CIM管理手順書案_未承認.xlsx"),
        "sheets": [
            "用語",
            "構成と管理情報",
            "管理体制",
            "チェックシート(月次・異常時)",
            "要確認事項一覧",
        ],
    },
    "LNB": {
        "path": os.path.join(VAULT, "LNB管理手順書案_未承認.xlsx"),
        "sheets": [
            "表紙",
            "目次",
            "用語",
            "相関図",
            "相関図_old",
            "管理体制",
            "バックアップ",
            "復旧",
            "異常時の対応",
            "チェックシート(月次・異常時)",
            "会議課題一覧(一時)",
            "要確認事項一覧",
        ],
    },
}

ILLEGAL = '\\/:*?"<>|'


def sanitize(name: str) -> str:
    for c in ILLEGAL:
        name = name.replace(c, "_")
    return name


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    results = {"books": [], "errors": []}

    app = win32.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    try:
        for book_key, spec in BOOKS.items():
            book_dir = os.path.join(OUT, book_key)
            os.makedirs(book_dir, exist_ok=True)
            entry = {"book": book_key, "path": spec["path"], "sheets": []}
            wb = app.Workbooks.Open(spec["path"], ReadOnly=True)
            try:
                # 読み取り専用開帳では AutoSaveOn は設定不可(初回render_survey.pyで確認済み)。
                # 保存は一切行わないため原本は保護される。
                for sheet_name in spec["sheets"]:
                    ws = wb.Worksheets(sheet_name)
                    pdf_path = os.path.join(book_dir, sanitize(sheet_name) + ".pdf")
                    rec = {"sheet": sheet_name, "pdf": pdf_path}
                    try:
                        ws.ExportAsFixedFormat(
                            0,     # xlTypePDF
                            pdf_path,
                            0,     # xlQualityStandard
                            True,  # IncludeDocProperties
                            False, # IgnorePrintAreas=False(印刷範囲を尊重)
                        )
                        rec["ok"] = os.path.exists(pdf_path)
                    except Exception as e:  # noqa: BLE001
                        rec["ok"] = False
                        rec["error"] = repr(e)
                        results["errors"].append(f"{book_key}/{sheet_name}: {e!r}")
                    entry["sheets"].append(rec)
            finally:
                wb.Close(SaveChanges=False)
            results["books"].append(entry)
    finally:
        app.Quit()

    result_path = os.path.join(OUT, "render_result_rest.json")
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("WROTE", result_path)
    for b in results["books"]:
        for s in b["sheets"]:
            print(b["book"], s["sheet"], "ok" if s.get("ok") else s.get("error"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
