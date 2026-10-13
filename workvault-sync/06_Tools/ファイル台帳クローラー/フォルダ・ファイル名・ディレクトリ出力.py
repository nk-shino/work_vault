# -*- coding: utf-8 -*-
"""
�?定ディレクトリ配下�?�フォルダ・ファイル一覧�? Markdown にまとめる�?
出力�?�が存在すれば更新?��上書き）、なければ新規作�?�する�?
"""

import os
from datetime import datetime

# ==== 設�? ====================================================
# 対象�?ィレクトリ?��末尾に \ は付けな�? / �?�? r"..." で囲む?�?
TARGET_DIR = r"\\C:\Users\ss80751\OneDrive - NK\�h�L�������g\Work_Vault"

# 出力す�? .md ファイルのパス?���??ファイル名まで�?�? / �?�? r"..." で囲む?�?
OUTPUT_MD = r"C:\Users\ss80751\OneDrive - NK\ドキュメン�?\Work_Vault\00_inbox\�?原フォルダ一覧.md"
# =============================================================


def human_size(num_bytes):
    """バイト数を読み�?すい単位に変換"""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if num_bytes < 1024:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} PB"


def main():
    lines = []
    lines.append("# ファイル・フォルダ一覧")
    lines.append("")
    lines.append(f"- **対象�?ィレクトリ**: `{TARGET_DIR}`")
    lines.append(f"- **取得日�?**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    total_dirs = 0
    total_files = 0

    if not os.path.exists(TARGET_DIR):
        print(f"[エラー] 対象�?ィレクトリが見つかりません: {TARGET_DIR}")
        print("パス�?ネットワーク接続、アクセス権を確認してください�?")
        return

    # --- �?リー構�?セクション ---
    lines.append("## �?ィレクトリ構�?")
    lines.append("")
    lines.append("```text")

    for root, dirs, files in os.walk(TARGET_DIR):
        rel = os.path.relpath(root, TARGET_DIR)
        depth = 0 if rel == "." else rel.count(os.sep) + 1
        indent = "    " * depth

        folder_name = os.path.basename(root) if rel != "." else os.path.basename(TARGET_DIR)
        lines.append(f"{indent}[DIR] {folder_name}/")
        total_dirs += 1

        dirs.sort()
        for f in sorted(files):
            lines.append(f"{indent}    {f}")
            total_files += 1

    lines.append("```")
    lines.append("")

    # --- 詳細一覧セクション ---
    lines.append("## 詳細一覧?��相対パス・更新日時�?�サイズ?�?")
    lines.append("")
    lines.append("| 種別 | 相対パス | 更新日�? | サイズ |")
    lines.append("| --- | --- | --- | --- |")

    for root, dirs, files in os.walk(TARGET_DIR):
        dirs.sort()
        rel_root = os.path.relpath(root, TARGET_DIR)

        rel_folder = "." if rel_root == "." else rel_root
        try:
            mtime = datetime.fromtimestamp(os.path.getmtime(root)).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            mtime = "-"
        lines.append(f"| フォルダ | `{rel_folder}` | {mtime} | - |")

        for f in sorted(files):
            full = os.path.join(root, f)
            rel_path = os.path.relpath(full, TARGET_DIR)
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(full)).strftime("%Y-%m-%d %H:%M:%S")
                size = human_size(os.path.getsize(full))
            except Exception:
                mtime, size = "-", "-"
            lines.append(f"| ファイル | `{rel_path}` | {mtime} | {size} |")

    # --- サマリ ---
    lines.insert(4, f"- **フォルダ数**: {total_dirs} / **ファイル数**: {total_files}")

    # --- 出力（存在すれば更新?��なければ新規作�?��?---
    os.makedirs(os.path.dirname(OUTPUT_MD), exist_ok=True)
    is_update = os.path.exists(OUTPUT_MD)

    with open(OUTPUT_MD, "w", encoding="utf-8") as fp:
        fp.write("\n".join(lines))

    action = "更新?��上書き�?" if is_update else "新規作�??"
    print(f"[完�?] {OUTPUT_MD} を{action}しました�?")
    print(f"フォルダ数: {total_dirs} / ファイル数: {total_files}")


if __name__ == "__main__":
    main()