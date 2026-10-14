# -*- coding: utf-8 -*-
"""
指定ディレクトリ配下のフォルダ・ファイル一覧を Markdown にまとめる。
更新日時・サイズも記録し、後のバックアップ差分同期に活用できるようにする。
出力先が存在すれば更新（上書き）、なければ新規作成する。
"""

import os
from datetime import datetime

# ==== 設定 ====================================================
# 対象ディレクトリ（末尾に \ は付けない）
TARGET_DIR = r"\\nksv569.ad.nkc.co.jp\Share\mnt\DGS-SV\★個人フォルダ\篠原"

# 出力する .md ファイルのパス（★ファイル名まで指定すること）
OUTPUT_MD = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\00_inbox\篠原フォルダ一覧.md"
# =============================================================


def human_size(num_bytes):
    """バイト数を読みやすい単位に変換"""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if num_bytes < 1024:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} PB"


def main():
    lines = []
    lines.append("# ファイル・フォルダ一覧")
    lines.append("")
    lines.append(f"- **対象ディレクトリ**: `{TARGET_DIR}`")
    lines.append(f"- **取得日時**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    total_dirs = 0
    total_files = 0

    if not os.path.exists(TARGET_DIR):
        print(f"[エラー] 対象ディレクトリが見つかりません: {TARGET_DIR}")
        print("パスやネットワーク接続、アクセス権を確認してください。")
        return

    # --- ツリー構造セクション ---
    lines.append("## ディレクトリ構造")
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

    # --- 詳細一覧セクション（更新日時・サイズ付き / 差分同期用）---
    lines.append("## 詳細一覧（相対パス・更新日時・サイズ）")
    lines.append("")
    lines.append("| 種別 | 相対パス | 更新日時 | サイズ |")
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

    # --- 出力（存在すれば更新／なければ新規作成）---
    # 出力先フォルダがなければ作成
    os.makedirs(os.path.dirname(OUTPUT_MD), exist_ok=True)

    # ★ ファイルの存在チェック（更新 or 新規作成の判定）
    is_update = os.path.exists(OUTPUT_MD)

    # "w" モードは「存在すれば上書き（＝更新）、なければ新規作成」の両方に対応
    with open(OUTPUT_MD, "w", encoding="utf-8") as fp:
        fp.write("\n".join(lines))

    action = "更新（上書き）" if is_update else "新規作成"
    print(f"[完了] {OUTPUT_MD} を{action}しました。")
    print(f"フォルダ数: {total_dirs} / ファイル数: {total_files}")


if __name__ == "__main__":
    main()
