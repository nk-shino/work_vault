# -*- coding: utf-8 -*-
"""各 open issue に最適合 Kohden Code セッションへのリンクをコメントする。"""
import json, subprocess, sys, time, urllib.request

# ---- token ----
def get_token():
    p = subprocess.run(["git", "credential", "fill"],
                       input="protocol=https\nhost=github.com\n\n",
                       capture_output=True, text=True)
    for line in p.stdout.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    raise SystemExit("no token")

# ---- sessions (id -> title, updated, dir) ----
with open(r"C:\Users\ss80751\kohden-code-workspace\20261013_issue-kanban-ops\sessions_dump.json", encoding="utf-8") as f:
    sessions = {s["id"]: s for s in json.load(f)}

def fmt_date(ms):
    return time.strftime("%Y/%m/%d", time.localtime(ms / 1000))

def dir_short(d):
    return "ワークスペース" if "kohden-code-workspace" in d else "Work_Vault"

# ---- mapping: issue -> (session_id, 適合理由) or (None, 理由, [参考session]) ----
M = {
 2:  ("ses_ee1753de4ffeKNc1dlHP0AbrBa", "ver2 セット一式と課題管理表の検証を本セッションで実施。テストシナリオ確定の基礎"),
 3:  ("ses_ec83f477bffewTlKY8E9aNSUTT", "管理書・手順書モック（横書き様式）の新規作成を本セッションで実施"),
 4:  ("ses_eaddea894fferOv0GbFmbsh3bd", "TOOL系 xlam の仕様抽出を実施。容量確認機能の要件整理の出発点"),
 6:  (None, "会議・関係者確認が前提", ["ses_eadde898fffeiUpH6yUSMy8FXe"]),
 7:  (None, "関係者への報告が前提", ["ses_ee174f99affeZTZqAeyPJgsTve"]),
 8:  (None, "pptx 図解作成の該当セッションなし", ["ses_ec6e48b32ffeWscnC1L2MiYeyd"]),
 9:  ("ses_ee102b833ffetbwEiia1edsKwr", "業務報告の根拠調査で B列修正の経緯（佐藤さん作業由来）を照合済み"),
 10: ("ses_ebd917abeffetGJaeu7GLhITgF", "鹿島引き込みの既存プログラム所在確認を実施。改修検討の前提資料"),
 11: (None, "本人確認・調査が前提", ["ses_ec1ad58a7ffeWVtzSoS4bd1luC"]),
 12: (None, "規程確認は社内規程の参照が前提", []),
 13: (None, "モデル選定の該当セッションなし", []),
 14: ("ses_ee174f99affeZTZqAeyPJgsTve", "0確認マクロのコード検証（採用版判定の根拠）を実施"),
 15: ("ses_ee174f99affeZTZqAeyPJgsTve", "0確認マクロのコード検証で Trim/空白の扱いに触れた箇所あり"),
 16: ("ses_ee174f99affeZTZqAeyPJgsTve", "0確認マクロのコード検証で B列制御に触れた箇所あり"),
 17: (None, "権限申請は社内手続きが前提", []),
 18: ("ses_ec18dbaf3ffeTNNyOViPSWgtR3", "ディレクトリ合計サイズの計測方法を本セッションで確立（削除判断の材料）"),
 19: ("ses_ee6c2b65cfferivEhpL2003fw5", "Skill.md の作成と配置の実績あり。P2 Skills 作成の雛形"),
 20: ("ses_ee600fb32ffejMt0emaYuDltSm", "台帳収集スクリプト（ファイル台帳クローラー）の作成セッション"),
 21: (None, "転送自体は実施済み（起票元は kanban オーケストレーション）", ["ses_ee1780d7dffejh184S2UlPAd1i"]),
 24: ("ses_ebde287f7ffe350k304fxkauqk", "テキスト情報（統合正本）の整理を本セッションで実施"),
 25: (None, "本人判断が前提", []),
 28: ("ses_ee600fb32ffejMt0emaYuDltSm", "クローラー（台帳収集スクリプト）の作成セッション。検知強化の改修先"),
 29: (None, "設計前・該当セッションなし", []),
 30: (None, "社用PCでの検証が前提", []),
 32: (None, "技術選定の該当セッションなし", []),
 33: ("ses_ee64ed521ffegqAXeH0iFXcAdZ", "外部 MCP 導入のルール確認を実施。LearningSkill 改修の制約条件"),
 34: (None, "導入検討の該当セッションなし", []),
 35: (None, "PanaCIM 実機調査が前提", ["ses_ecc8d34f1ffeRvagS8wmWRSAl5"]),
 36: ("ses_ec6e48b32ffeWscnC1L2MiYeyd", "データフロー相関図（PanaCIM/LNB）の作図を本セッションで実施"),
 37: ("ses_ecc8d34f1ffeRvagS8wmWRSAl5", "点検項目・チェックシートの構成論を本セッションで整理"),
 38: (None, "様式化の該当セッションなし", ["ses_ec83f477bffewTlKY8E9aNSUTT"]),
 39: (None, "テンプレ初期値の確認は運用判断", ["ses_ee6c2b65cfferivEhpL2003fw5"]),
 40: (None, "スキル適用可否のレビューは運用判断", ["ses_ee1780d7dffejh184S2UlPAd1i"]),
 41: (None, "スキャン・規程確認は社内手続きが前提", []),
 42: (None, "実LNB端末での作業が前提（Vault 側セッションは本文未保存のため参照不可）", []),
 43: ("ses_ecc3d3782ffeEPBeMG5tMkTdPt", "ver2 の仕様書整備と品質改善を本セッションで実施。実機検証の直前工程"),
 44: (None, "本人判断待ち3件の処理", ["ses_ee1753de4ffeKNc1dlHP0AbrBa"]),
 45: (None, "他者との突合が前提", []),
 46: (None, "会議記録の確認と反映判断", []),
 47: (None, "本人判断・管理書反映", ["ses_ec1ad58a7ffeWVtzSoS4bd1luC"]),
 48: ("ses_ecd6d06eaffe2xB2hTFAEEiD3t", "利用状況の分析と可視化を本セッションで実施。Power BI 連携の延長"),
 49: ("ses_ee60074feffewl0GDJilr0843e", "OCR 抽出スクリプトの作成セッション。抽出画像精査の直接の続き"),
 50: ("ses_ee102b833ffetbwEiia1edsKwr", "業務報告の根拠調査と進捗検証を本セッションで実施（報告本体の作成元）"),
 52: ("ses_ec2baa893ffeAlqHrU55ENKylX", "設計解析と品質検証（判明事実の抽出方法）を実施。K-01〜K-14 対応の手法参照"),
 53: ("ses_eaddea894fferOv0GbFmbsh3bd", "TOOL系 xlam の仕様抽出で本体/コピーの2版を確認済み"),
 54: ("ses_ee174f99affeZTZqAeyPJgsTve", "0確認マクロのコード検証を実施。運用反映の内容確認の基礎"),
 55: ("ses_ee1753de4ffeKNc1dlHP0AbrBa", "不足情報12項目を含む課題管理表の検証を本セッションで実施"),
 56: ("ses_ec83f477bffewTlKY8E9aNSUTT", "レビュー対象の管理書・手順書案（横書き様式）を作成したセッション"),
 57: (None, "社用PCでの検証と判断が前提", []),
 58: ("ses_ec83f477bffewTlKY8E9aNSUTT", "管理手順書案の作成元セッション。レビュー・初版登録の対象"),
 59: ("ses_ee1780d7dffejh184S2UlPAd1i", "2026-10-20 の初回記載（10月セル+アクション列）を実施したセッション"),
 60: ("ses_ebd917abeffetGJaeu7GLhITgF", "鹿島引き込みの既存プログラム確認を実施。導入時運用確認の前提"),
}

token = get_token()
repo = "nk-shino/task-board"

def post_comment(num, body):
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/issues/{num}/comments",
        data=json.dumps({"body": body}).encode("utf-8"),
        headers={"Authorization": f"token {token}",
                 "Accept": "application/vnd.github+json",
                 "Content-Type": "application/json"},
        method="POST")
    with urllib.request.urlopen(req) as r:
        return json.load(r)["html_url"]

def ref(s):
    ss = sessions[s]
    return "「%s」（%s 更新・%s）`%s`" % (ss["title"], fmt_date(ss["updated"]), dir_short(ss["dir"]), ss["id"])

issues = json.loads(subprocess.run(
    ["gh", "issue", "list", "-R", repo, "--state", "open", "--limit", "100", "--json", "number"],
    capture_output=True, text=True, encoding="utf-8").stdout)
nums = sorted(i["number"] for i in issues["numbers"] if False) if False else sorted(i["number"] for i in issues)

posted = 0
for num in nums:
    m = M.get(num)
    if m is None:
        body = "## 関連 Kohden Code セッション\n\n- 直接の該当セッションなし（全52件の走査対象外・本 issue 固有の文脈）。\n"
        continue
    if m[0] is None:
        reason, refs = m[1], m[2]
        lines = ["## 関連 Kohden Code セッション\n",
                 "- 直接の該当セッションなし（%s）。" % reason]
        for r in refs:
            lines.append("- 参考（最も近い）: %s" % ref(r))
        body = "\n".join(lines) + "\n"
    else:
        sid, reason = m
        body = ("## 関連 Kohden Code セッション（最適合）\n\n"
                "- %s\n"
                "- 復元: `kohden-code --session %s`\n"
                "- 適合理由: %s\n"
                "- 注: 共有URL（share）は未使用のため、ローカルのセッション参照リンク。\n"
                "  該当プロジェクトのディレクトリで kohden-code を起動するとセッション一覧からも選択できる。" % (ref(sid), sid, reason))
    url = post_comment(num, body)
    posted += 1
    print(num, "posted", url)

print("total posted:", posted)
