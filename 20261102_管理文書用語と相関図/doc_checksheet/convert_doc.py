# -*- coding: utf-8 -*-
"""NR6010T0101/T0201(.doc)を Word COM でテキスト化する。
出力先は一時領域 TEMP のみ(ワークスペース・git へは一切書かない)。
出力は文字数のみ。内容は標準出力へ書かない。"""
import os
import shutil
import time

SRC_DIR = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB"
FILES = ["NR6010T0101.doc", "NR6010T0201.doc"]
TMP = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\doc_checksheet"

os.makedirs(TMP, exist_ok=True)


def copy_retry(src, dst, tries=6):
    last = None
    for i in range(tries):
        try:
            shutil.copy2(src, dst)
            return
        except PermissionError as exc:
            last = exc
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"copy failed (OneDrive lock?): {src}") from last


import win32com.client as wc  # noqa: E402

word = wc.Dispatch("Word.Application")
word.Visible = False
word.DisplayAlerts = 0
results = []
try:
    for name in FILES:
        local = os.path.join(TMP, name)
        copy_retry(os.path.join(SRC_DIR, name), local)
        doc = word.Documents.Open(local, False, True)  # ConfirmConversions, ReadOnly
        base = os.path.join(TMP, name[:-4])
        doc.SaveAs2(base + ".txt", 7)   # wdFormatUnicodeText
        doc.SaveAs2(base + ".docx", 12)  # wdFormatXMLDocument(表構造の解析用)
        doc.Close(False)
        with open(base + ".txt", encoding="utf-16") as f:
            n = len(f.read())
        results.append((name, n))
finally:
    word.Quit()

for name, n in results:
    print(f"{name}: {n} chars -> TEMP txt/docx")
