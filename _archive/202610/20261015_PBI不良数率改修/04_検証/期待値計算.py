# -*- coding: utf-8 -*-
"""
第4段階 検証用: 期待値計算スクリプト(独立集計)
- ソースExcelを直接読み取り(中間CSVを使わない独立経路)
- 第2段階で合意した計算定義どおりに期待値を算出し、検証表(JSON+Markdown)を出力
- 使い方: python 期待値計算.py
- 出力: 期待値_YYYYMMDD_HHMMSS.json / 期待値_YYYYMMDD_HHMMSS.md (本スクリプトと同じフォルダ)
"""
import openpyxl
import json
import datetime
import io
import sys
from collections import defaultdict

# Windows コンソールでも安全に出力
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

SRC = (
    r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般"
    r"\新規可視化システム\500_後工程関連\500_後工程関連\２.AOI直行率\日報\部品別(虚報).xlsx"
)
CAUSES = ["位置ズレ", "半田不足", "浮き", "ブリッジ", "寸法",
          "極性不良", "OCV", "欠品", "表裏反転", "異物", "Falut"]

# 列定義(0始まり): A=0 .. R=17
C_PKG, C_KENSA, C_RYOHIN, C_FURYO = 0, 1, 2, 3
C_LEV, C_KYOHO, C_NG = 15, 16, 17


def load_rows():
    """日報(部品別(虚報).xlsx)の全日付シートを縦持ちリストへ。
    1行 = {日付, パッケージ, 検査数, 良品数, 不良数, 原因{...}, 虚報数, NG数}
    小計・合計行は存在しない(第1段階で実測・B=C+D検算済み)。"""
    wb = openpyxl.load_workbook(SRC, read_only=True, data_only=True)
    rows = []
    for sn in wb.sheetnames:
        if not (sn.isdigit() and len(sn) == 8):
            continue  # 空のSheet1等を除外
        day = f"{sn[:4]}-{sn[4:6]}-{sn[6:]}"
        for r in wb[sn].iter_rows(min_row=2, values_only=True):
            if r[C_PKG] is None:
                continue
            rows.append({
                "日付": day,
                "パッケージ": str(r[C_PKG]),
                "検査数": int(r[C_KENSA] or 0),
                "良品数": int(r[C_RYOHIN] or 0),
                "不良数": int(r[C_FURYO] or 0),
                "原因": {c: int(r[4 + i] or 0) for i, c in enumerate(CAUSES)},
                "虚報数": int(r[C_KYOHO] or 0),
                "NG数": int(r[C_NG] or 0),
            })
    wb.close()
    return rows


def pct(num, den):
    """率: 小数3桁(合意定義)。分母ゼロは None(=Power BI上は空白表示)"""
    return round(num / den * 100, 3) if den else None


def main():
    rows = load_rows()
    exp = {"生成時刻": datetime.datetime.now().isoformat(timespec="seconds"),
           "ソース": SRC, "行数": len(rows), "検証": []}

    # --- V-01: 全期間カード値 ------------------------------------------
    k = sum(r["検査数"] for r in rows)
    kyo = sum(r["虚報数"] for r in rows)
    ng = sum(r["NG数"] for r in rows)
    exp["検証"].append({"検証ID": "V-01", "対象要件": "カード(全期間)",
        "条件": "フィルターなし",
        "期待値": {"検査数": k, "虚報数": kyo, "NG数": ng,
                   "虚報率": pct(kyo, k), "NG率": pct(ng, k)}})

    # --- V-02: 原因別パレート(全原因・降順・累積率) ----------------------
    cs = {c: sum(r["原因"][c] for r in rows) for c in CAUSES}
    total_bad = sum(cs.values())
    assert total_bad == sum(r["不良数"] for r in rows), "原因合計≠不良数"
    cum, pareto = 0, []
    for c, v in sorted(cs.items(), key=lambda x: (-x[1], x[0])):
        cum += v
        pareto.append({"原因": c, "件数": v,
                       "構成率": round(v / total_bad * 100, 2) if total_bad else None,
                       "累積率": round(cum / total_bad * 100, 2) if total_bad else None})
    exp["検証"].append({"検証ID": "V-02", "対象要件": "原因別パレート",
        "条件": "フィルターなし・全11原因表示",
        "期待値": pareto,
        "確認点": "表示順=件数降順(同数は名前昇順)・最終累積率100.00%(総数>0のため必須)"})

    # --- V-03: 日別虚報数・NG数(折れ線用・全日付) -----------------------
    by_day = defaultdict(lambda: [0, 0, 0])
    for r in rows:
        d = by_day[r["日付"]]
        d[0] += r["検査数"]; d[1] += r["虚報数"]; d[2] += r["NG数"]
    daily = [{"日付": d, "検査数": v[0], "虚報数": v[1], "NG数": v[2],
              "虚報率": pct(v[1], v[0]), "NG率": pct(v[2], v[0])}
             for d, v in sorted(by_day.items())]
    exp["検証"].append({"検証ID": "V-03", "対象要件": "日別折れ線/積み上げ棒",
        "条件": "フィルターなし", "日数": len(daily), "期待値": daily})

    # --- V-04: パッケージ別(表・不良数降順 上位10) ----------------------
    by_pkg = defaultdict(lambda: [0, 0, 0, 0])
    for r in rows:
        p = by_pkg[r["パッケージ"]]
        p[0] += r["検査数"]; p[1] += r["虚報数"]; p[2] += r["NG数"]; p[3] += r["不良数"]
    top = [{"パッケージ": p, "検査数": v[0], "虚報数": v[1], "NG数": v[2],
            "不良数": v[3], "虚報率": pct(v[1], v[0]), "NG率": pct(v[2], v[0])}
           for p, v in sorted(by_pkg.items(), key=lambda x: (-x[1][3], x[0]))[:10]]
    exp["検証"].append({"検証ID": "V-04", "対象要件": "パッケージ別表(不良数降順上位10)",
        "条件": "フィルターなし", "期待値": top,
        "確認点": "A列全体を軸とする(合意)。パッケージ名部分の分割は第1版非採用"})

    # --- V-05: 虚報率上位(検査数>=100) ---------------------------------
    top_rate = [{"パッケージ": p, "検査数": v[0], "虚報率": pct(v[1], v[0]), "NG率": pct(v[2], v[0])}
                for p, v in sorted(((p, v) for p, v in by_pkg.items() if v[0] >= 100),
                                   key=lambda x: (-(x[1][1] / x[1][0]), x[0]))[:10]]
    exp["検証"].append({"検証ID": "V-05", "対象要件": "虚報率上位表",
        "条件": "検査数>=100", "期待値": top_rate})

    # --- V-06: 特定日フィルター(スライサー動作確認・最初日と最終日) ------
    for day in (min(by_day), max(by_day)):
        sub = [r for r in rows if r["日付"] == day]
        k2 = sum(r["検査数"] for r in sub)
        kyo2 = sum(r["虚報数"] for r in sub)
        ng2 = sum(r["NG数"] for r in sub)
        exp["検証"].append({"検証ID": "V-06", "対象要件": "日付スライサー",
            "条件": f"日付={day}", "期待値": {"検査数": k2, "虚報数": kyo2, "NG数": ng2,
            "虚報率": pct(kyo2, k2), "NG率": pct(ng2, k2)}})

    # --- V-07: 特定パッケージの原因内訳(E〜O列の表照合) -----------------
    worst = max(by_pkg, key=lambda p: by_pkg[p][3])
    sub = [r for r in rows if r["パッケージ"] == worst]
    exp["検証"].append({"検証ID": "V-07", "対象要件": "原因別内訳(表)",
        "条件": f"パッケージ={worst}(不良数最大)",
        "期待値": {c: sum(r["原因"][c] for r in sub) for c in CAUSES}})

    # --- 出力 ----------------------------------------------------------
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    jpath = f"期待値_{ts}.json"
    mpath = f"期待値_{ts}.md"
    with open(jpath, "w", encoding="utf-8") as f:
        json.dump(exp, f, ensure_ascii=False, indent=1)

    md = [f"# 期待値(独立集計) {ts}", "",
          f"ソース: `{SRC}`  /  行数: {len(rows)}", ""]
    for v in exp["検証"]:
        md.append(f"## {v['検証ID']} {v['対象要件']}  (条件: {v.get('条件','')})")
        md.append("```json")
        md.append(json.dumps(v["期待値"], ensure_ascii=False, indent=1))
        md.append("```")
        if v.get("確認点"):
            md.append(f"確認点: {v['確認点']}")
        md.append("")
    with open(mpath, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    print(f"OK: {jpath} / {mpath}")
    print(f"全期間: 検査数={k} 虚報数={kyo} NG数={ng} 虚報率={pct(kyo,k)} NG率={pct(ng,k)}")


if __name__ == "__main__":
    main()
