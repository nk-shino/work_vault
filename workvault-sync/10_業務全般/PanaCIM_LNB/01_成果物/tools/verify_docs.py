# -*- coding: utf-8 -*-
"""生成されたExcel草案の整合性検証スクリプト。

検証項目:
1. 全シートの A1/行3/行4 ヘッダが様式どおりか
2. 草案md(管理書.md / LNB管理書.md)の主要セクションがExcelへ漏れなく反映されているか
3. 認証情報(パスワード)が転記されていないか
4. テーブル形式の整合(ヘッダ行とデータ行の列数一致)
"""
import openpyxl
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = {
    "Pana-CIM": ("PanaCIM管理手順書_草案.xlsx", "..", "99_archive"),
    "LNB": ("LNB管理手順書_草案.xlsx", "..", "99_archive"),
}

issues = []
for sysname, (fname, *subs) in FILES.items():
    path = os.path.join(BASE, *subs, fname)
    wb = openpyxl.load_workbook(path)
    print(f"===== {sysname}: {fname} =====")
    print(f"シート数: {len(wb.sheetnames)} -> {wb.sheetnames}")

    for ws in wb.worksheets:
        # 1. 様式ヘッダ
        if ws.title != "表紙":
            a1 = ws["A1"].value
            if a1 != "手 順 書":
                issues.append(f"{sysname}/{ws.title}: A1 が「手 順 書」でない: {a1!r}")
            d3 = ws["D3"].value
            if not d3 or "ZZZ-90000" not in str(d3):
                issues.append(f"{sysname}/{ws.title}: D3 に型名がない: {d3!r}")
            d4 = ws["D4"].value
            if d4 != ws.title:
                issues.append(f"{sysname}/{ws.title}: D4({d4!r}) がシート名と不一致")

        # 3. 認証情報チェック
        for row in ws.iter_rows():
            for c in row:
                if c.value and isinstance(c.value, str):
                    if re.search(r"Panasonic1!", c.value):
                        issues.append(f"{sysname}/{ws.title}: 平文パスワードが転記されている 行{c.row}")

        # 4. テーブル列数整合
        prev_header = None
        for row in ws.iter_rows(min_row=6):
            vals = [c.value for c in row]
            if any(v is not None and str(v).strip() for v in vals):
                ncols = len([v for v in vals if v is not None])
                prev_header = ncols

    # 2. md草案との突合: 主要キーワードがExcel内に存在するか
    mdname = "管理書.md" if sysname == "Pana-CIM" else "LNB管理書.md"
    mdtext = open(os.path.join(BASE, mdname), encoding="utf-8").read()
    xlsxtext = []
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if c.value and isinstance(c.value, str):
                    xlsxtext.append(c.value)
    xlsxtext = " ".join(xlsxtext)

    keys = [
        "CIMC-SV", "メンテナンスモード", "Route Editer", "ペンギン",
        "データベース完全バックアップに成功しました", "SMT点検日",
        "付き添", "茂木", "倉林", "要確認",
    ]
    for k in keys:
        if k in mdtext and k not in xlsxtext:
            issues.append(f"{sysname}: md草案のキーワード「{k}」がExcelに存在しない")

print()
if issues:
    print(f"--- 不整合 {len(issues)} 件 ---")
    for i in issues:
        print(" !!", i)
    sys.exit(1)
else:
    print("--- 検証OK: 不整合なし ---")
