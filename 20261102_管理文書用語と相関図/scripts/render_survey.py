# -*- coding: utf-8 -*-
"""
render_survey.py — 管理手順書2冊の代表シートをPDF化して印刷体裁を点検する。
- Excel COM: 読み取り専用で開く / AutoSaveOn=False を明示 / 保存しない
- 出力先: render_survey/ 配下のみ
- 冊・dump・その他のファイルは変更しない
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
            "表紙",
            "目次",
            "相関図",
            "相関図_old",
            "月次再起動",
            "バックアップ",
            "復旧",
            "異常時の対応",
            "会議課題一覧(一時)",
            "付録 引用元と確認範囲",
            "7-5仮_サービス起動停止",
        ],
    },
    "LNB": {
        "path": os.path.join(VAULT, "LNB管理手順書案_未承認.xlsx"),
        "sheets": [
            "構成と管理情報",
            "日次点検",
            "定期管理",
            "チェックシート(日次)",
            "引用と部品照合",
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
                try:
                    wb.AutoSaveOn = False
                    entry["autosaveon"] = "set_false"
                except Exception as e:  # noqa: BLE001
                    # 読み取り専用開帳では AutoSaveOn が設定不可(=AutoSave無効)のため記録して続行。
                    # 保存は一切行わないため原本は保護される。
                    entry["autosaveon"] = f"not_settable_readonly: {e!r}"
                # 全シート名の実測(分類表の根拠用)
                entry["sheet_names_actual"] = [ws.Name for ws in wb.Worksheets]
                for sheet_name in spec["sheets"]:
                    ws = wb.Worksheets(sheet_name)
                    pdf_path = os.path.join(book_dir, sanitize(sheet_name) + ".pdf")
                    rec = {"sheet": sheet_name, "pdf": pdf_path}
                    try:
                        ws.ExportAsFixedFormat(
                            0,  # xlTypePDF
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

    result_path = os.path.join(OUT, "render_result.json")
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("WROTE", result_path)
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
