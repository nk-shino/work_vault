# -*- coding: utf-8 -*-
import sys, json
sys.stdout.reconfigure(encoding='utf-8')
out_dir = r"C:\Users\ss80751\kohden-code-workspace\20261016_鹿島引き込みExcel分析"
run_id = "run-20261016-kashima-hikikomi-01"
rev = "R1"


def obj(oid, kind, label, evs, state="confirmed_in_source"):
    return {"object_id": oid, "class": "content", "kind": kind, "label": label, "state": state, "evidence_ids": evs}


objects = [
    obj("OBJ-01", "file", "差分確認マクロver2.3a.xlsm", ["EV-001"]),
    obj("OBJ-02", "sheet", "sabun(差分元データ・非表示)", ["EV-011", "EV-012"]),
    obj("OBJ-03", "sheet", "BOM作成(Asprova製造BOMテンプレート)", ["EV-018", "EV-019"]),
    obj("OBJ-04", "sheet", "差分1-6(指図別チェック表・計1-6と対)", ["EV-013", "EV-016", "EV-027"]),
    obj("OBJ-05", "sheet", "計画1-6(指図完了記録)", ["EV-014", "EV-015", "EV-017"]),
    obj("OBJ-06", "sheet", "差分x/計画x(複製元テンプレート・非表示)", ["EV-001", "EV-005"]),
    obj("OBJ-07", "figure", "リボンタブ「差分チェック」(customUI)", ["EV-002"]),
    obj("OBJ-08", "documented_entity", "VBAモジュール群(Module1/tools/指図入力/シート18個)", ["EV-003", "EV-004", "EV-005", "EV-006", "EV-007", "EV-008", "EV-009", "EV-010"]),
    obj("OBJ-09", "documented_entity", "sabun.csv(nksv523・取込既定ファイル)", ["EV-023", "EV-003"]),
    obj("OBJ-10", "documented_entity", "差分チェックシステム(sashizu.cgi)", ["EV-004", "EV-024"]),
    obj("OBJ-11", "documented_entity", "段取り予定.xlsx(SharePoint)", ["EV-005", "EV-024"]),
    obj("OBJ-12", "documented_entity", "JOB作成関連マクロ→TOOL.xlam(差分明細生成)", ["EV-025", "EV-026", "EV-024"]),
    obj("OBJ-13", "documented_entity", "差分確認手順書.xlsx", ["EV-024"]),
    obj("OBJ-14", "documented_entity", "nksv523版コピー(マクロ等フォルダ)", ["EV-021", "EV-022"]),
]


def rel(rid, s, t, typ, d, label, evs):
    return {"relation_id": rid, "source_object_id": s, "target_object_id": t, "type": typ,
            "direction": d, "label": label, "state": "confirmed_in_source", "evidence_ids": evs}


relations = [
    rel("REL-01", "OBJ-01", "OBJ-02", "containment", "forward", "sabunシート", ["EV-001"]),
    rel("REL-02", "OBJ-01", "OBJ-03", "containment", "forward", "BOM作成シート", ["EV-001"]),
    rel("REL-03", "OBJ-01", "OBJ-04", "containment", "forward", "差分1-6シート", ["EV-001"]),
    rel("REL-04", "OBJ-01", "OBJ-05", "containment", "forward", "計画1-6シート", ["EV-001"]),
    rel("REL-05", "OBJ-01", "OBJ-06", "containment", "forward", "差分x/計画xシート", ["EV-001"]),
    rel("REL-06", "OBJ-01", "OBJ-07", "containment", "forward", "customUI", ["EV-002"]),
    rel("REL-07", "OBJ-01", "OBJ-08", "containment", "forward", "VBAプロジェクト", ["EV-001"]),
    rel("REL-08", "OBJ-09", "OBJ-02", "content_correspondence", "forward", "取込(CSV→sabunシート一括書込)", ["EV-003", "EV-023"]),
    rel("REL-09", "OBJ-02", "OBJ-04", "formula_reference", "forward", "INDEX/MATCH(差分n!B..J列)", ["EV-013"]),
    rel("REL-10", "OBJ-02", "OBJ-05", "content_correspondence", "forward", "C列判定 MATCH(計画n!A,差分n!A)", ["EV-008"]),
    rel("REL-11", "OBJ-04", "OBJ-05", "content_correspondence", "bidirectional", "番号対応ペア(差分n/計画n)", ["EV-010"]),
    rel("REL-12", "OBJ-06", "OBJ-04", "content_correspondence", "forward", "7件超時に複製し差分7..を生成", ["EV-005"]),
    rel("REL-13", "OBJ-06", "OBJ-05", "content_correspondence", "forward", "同上(計画側)", ["EV-005"]),
    rel("REL-14", "OBJ-04", "OBJ-10", "hyperlink", "forward", "NG行へsashizu.cgiリンク(J列)", ["EV-004"]),
    rel("REL-15", "OBJ-11", "OBJ-04", "content_correspondence", "forward", "ジョブ名+指図をA列へ転記(do_prepare)", ["EV-005"]),
    rel("REL-16", "OBJ-07", "OBJ-08", "content_correspondence", "forward", "リボンボタン→VBAマクロ", ["EV-002"]),
    rel("REL-17", "OBJ-08", "OBJ-04", "formula_reference", "forward", "差分NGにリンク貼る/ sabunTemplate / SashizuClear", ["EV-004", "EV-007", "EV-010"]),
    rel("REL-18", "OBJ-04", "OBJ-09", "content_correspondence", "forward", "output: 差分チェックn.csv 出力", ["EV-006"]),
    rel("REL-19", "OBJ-03", "OBJ-12", "document_reference", "forward", "BOM作成→Asprova用データ(画像で運用を示す)", ["EV-018", "EV-019"]),
    rel("REL-20", "OBJ-12", "OBJ-04", "content_correspondence", "forward", "差分明細テンプレ作成(差分CSV集計)", ["EV-024", "EV-025"]),
    rel("REL-21", "OBJ-13", "OBJ-01", "document_reference", "forward", "手順書が本ブックの運用を説明", ["EV-024"]),
    rel("REL-22", "OBJ-01", "OBJ-14", "duplicate_content", "bidirectional", "同一ブックの2拠点コピー", ["EV-021", "EV-022"]),
    rel("REL-23", "OBJ-03", "OBJ-03", "content_correspondence", "forward", "2ブロック構造(1-15行/18-28行)", ["EV-018"]),
]

pages = [
    {"page_id": "PG-01", "category": "overview", "title": "全体構成と目的", "scope": "ブック全体・外部連携の全体像", "reading_direction": "left_to_right"},
    {"page_id": "PG-02", "category": "content_structure", "title": "シート構成とデータ内容", "scope": "16シートの構成・列構造・現状値", "reading_direction": "left_to_right"},
    {"page_id": "PG-03", "category": "relationships", "title": "参照と連携の流れ", "scope": "シート間数式参照・VBA・外部ファイル", "reading_direction": "left_to_right"},
    {"page_id": "PG-04", "category": "issues", "title": "不整合と未確認事項", "scope": "今回確認した不整合・未確認", "reading_direction": "left_to_right"},
]

instances = []
for pg in pages:
    for o in objects:
        instances.append({"instance_id": "INS-%s-%s" % (pg["page_id"], o["object_id"]), "object_id": o["object_id"], "page_id": pg["page_id"], "native_cell_id": "%s_%s" % (pg["page_id"], o["object_id"])})

edges = []
rel_page = {"REL-01": "PG-02", "REL-02": "PG-02", "REL-03": "PG-02", "REL-04": "PG-02", "REL-05": "PG-02", "REL-06": "PG-02", "REL-07": "PG-02",
            "REL-08": "PG-03", "REL-09": "PG-03", "REL-10": "PG-03", "REL-11": "PG-03", "REL-12": "PG-03", "REL-13": "PG-03", "REL-14": "PG-03",
            "REL-15": "PG-03", "REL-16": "PG-03", "REL-17": "PG-03", "REL-18": "PG-03", "REL-19": "PG-03", "REL-20": "PG-03", "REL-21": "PG-03",
            "REL-22": "PG-04", "REL-23": "PG-02"}
for r in relations:
    pg = rel_page[r["relation_id"]]
    edges.append({"edge_id": "EDG-%s" % r["relation_id"], "relation_id": r["relation_id"], "page_id": pg,
                  "source_instance_id": "INS-%s-%s" % (pg, r["source_object_id"]),
                  "target_instance_id": "INS-%s-%s" % (pg, r["target_object_id"]),
                  "native_cell_id": "%s_%s" % (pg, r["relation_id"])})

issues = [
    {"issue_id": "ISS-01", "description": "Work_Vault版とnksv523版でBOM作成!B15の品目名が不一致(UR-4567 vs UR-4658)。", "severity": "medium", "status": "open",
     "affected_object_ids": ["OBJ-03", "OBJ-14"], "evidence_ids": ["EV-021"], "impact": "どちらが最新の作業状態か判断できない。片方だけの更新で差異が残る。"},
    {"issue_id": "ISS-02", "description": "nksv523版のModule1 p-codeが相違(ソース同一)。", "severity": "info", "status": "open",
     "affected_object_ids": ["OBJ-08", "OBJ-14"], "evidence_ids": ["EV-022"], "impact": "保存環境(Excelバージョン/保護状態)の違いで生成され得るが要因は未確認。動作差は確認されていない。"},
    {"issue_id": "ISS-03", "description": "ブック内sabunシート(173行・6/30以前)と sabun.csv(200行・10/16)の指図集合が不一致。", "severity": "info", "status": "open",
     "affected_object_ids": ["OBJ-02", "OBJ-09"], "evidence_ids": ["EV-023", "EV-011"], "impact": "シート内容は直近取込時点のスナップショット。現行の差分状況はCSV/システム側で確認する必要がある。"},
    {"issue_id": "ISS-04", "description": "差分1-5のJ列にNG(計6指図)があるが保存状態のハイパーリンクは0件。", "severity": "low", "status": "open",
     "affected_object_ids": ["OBJ-04"], "evidence_ids": ["EV-016", "EV-027"], "impact": "NG時に差分NGにリンク貼るがイベント等で再実行されれば付く。保存時点で未実行の可能性。"},
    {"issue_id": "ISS-05", "description": "計画2の230-264行D列に旧データ残骸(2024-02のタイムスタンプ16件)。", "severity": "low", "status": "open",
     "affected_object_ids": ["OBJ-05"], "evidence_ids": ["EV-017"], "impact": "S1_2の変更イベントはA列基準で消去するため残る。誤読の恐れは小さいが整理対象。"},
    {"issue_id": "ISS-06", "description": "名前定義 _xlpm.s が #NAME? で残存。", "severity": "info", "status": "open",
     "affected_object_ids": ["OBJ-01"], "evidence_ids": ["EV-020"], "impact": "LET関数引数名由来の副産物。動作への影響は確認していない。"},
    {"issue_id": "ISS-07", "description": "段取り予定.xlsx・差分チェックシステムの実体は今回未確認。", "severity": "info", "status": "open",
     "affected_object_ids": ["OBJ-10", "OBJ-11"], "evidence_ids": ["EV-005", "EV-024"], "impact": "連携先の仕様変更があった場合に本ブック側で検知できない。"},
]

graph = {
    "schema_version": "3.0", "run_id": run_id, "delivery_revision": rev,
    "artifact_id": "art-graph", "content_revision": rev,
    "limitations": ["行明細は代表値のみ。全行の列挙は supplemental_csv でなく台帳の範囲制約として要約記載。"],
    "objects": {"state": "complete", "scope": "対象ブックと直接確認した連携先を対象とした論理対象。", "limitations": ["計画2-6の行明細は要約。"], "items": objects},
    "relations": {"state": "complete", "scope": "確認できた参照・包含・対応・複製関係。", "limitations": [], "items": relations},
    "pages": {"state": "complete", "scope": "4ページ構成。", "limitations": [], "items": pages},
    "instances": {"state": "complete", "scope": "全ページ×全対象の再掲。", "limitations": [], "items": instances},
    "edges": {"state": "complete", "scope": "23関係の内、関係を表すコネクタ23本。", "limitations": [], "items": edges},
    "page_plan": {
        "revision": rev,
        "categories": [
            {"category": "overview", "selected": True, "reason": "全体像と連携先を最初に示す。"},
            {"category": "content_structure", "selected": True, "reason": "16シートの構造・列定義・現状値が分析の中核。"},
            {"category": "relationships", "selected": True, "reason": "数式参照・VBA・外部連携の経路が運用理解に必須。"},
            {"category": "format_and_print", "selected": False, "reason": "書式・印刷設定は条件付き書式とタブ色・用紙設定をissues/構成ページに統合し、単独ページにする量がない。"},
            {"category": "issues", "selected": True, "reason": "不整合(ISS-01〜06)と未確認(ISS-07)を明示する。"}
        ],
        "page_ids": ["PG-01", "PG-02", "PG-03", "PG-04"]
    }
}
json.dump(graph, open(out_dir + r"\ledger_graph.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump({"schema_version": "3.0", "run_id": run_id, "delivery_revision": rev, "artifact_id": "art-issues", "content_revision": rev,
           "limitations": [], "issues": {"state": "complete", "scope": "今回の分析で確認した不整合・未確認の全件。", "limitations": [], "items": issues}},
          open(out_dir + r"\ledger_issues.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("graph+issues written. objects:", len(objects), "relations:", len(relations), "edges:", len(edges), "issues:", len(issues))
