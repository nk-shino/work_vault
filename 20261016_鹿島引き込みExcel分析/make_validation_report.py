# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding='utf-8')

RUN_ID = "run-20261016-kashima-hikikomi-01"
REV = "R1"

report = {
 "schema_version": "3.0",
 "run_id": RUN_ID,
 "delivery_revision": REV,
 "artifact_id": "art-validation",
 "content_revision": "R1",
 "limitations": [
  "draw.io デスクトップが本機に未導入のため、保存ファイルのアプリ再読込・図形移動の接続追従テスト・物理印刷プレビューは実施していない。",
  "プレビューは drawio2svg(TypeScript)による実レンダリング。文字寸法は近似計測(Meiryo/CJK幅0.55倍)のため、アプリ側での最終目視確認を推奨。",
  "検査の実施主体はAI。人手確認は含まない。"
 ],
 "report_state": "final",
 "resolved_config": {
  "output_dir": "Work_Vault/10_業務全般/鹿島引き込み/業務内容",
  "preview_formats": ["svg"],
  "print_review_required": False,
  "max_correction_cycles": 2,
  "font": "Meiryo",
  "design": "rounded rect / orthogonal edges / 1169x826 page / spec default palette"
 },
 "resolution_log": [
  {"item": "output_dir", "resolved": "ユーザー指示により Work_Vault 10_業務全般/鹿島引き込み/業務内容 へ出力(Tier B・新規フォルダ作成)。"},
  {"item": "preview_formats", "resolved": "svg。PDFは変換ライブラリ不在のため未生成(理由を成果物台帳へ記録)。"},
  {"item": "drawio_open capability", "resolved": "draw.io desktop不在 → unavailable。renderer は npm @markdown-viewer/drawio2svg で代替し実行可能と確認。"}
 ],
 "configuration_history": [
  {"change_id": "CHG-01", "description": "REL-23(2ブロック構造)を自己参照コネクタから注記ラベル表現へ変更。", "affected": ["EDG-REL-23"]}
 ],
 "capabilities": [
  {"name": "local_parser", "status": "available", "basis": "Python3.13 xml.etree による drawio XML解析を実行し成功。"},
  {"name": "drawio_open", "status": "unavailable", "basis": "draw.io desktop未導入を確認(npx実行・インストール先探索ともに不在)。"},
  {"name": "renderer", "status": "available", "basis": "npm @markdown-viewer/drawio2svg で4ページのSVG生成に成功。"},
  {"name": "visual_review", "status": "unavailable", "basis": "SVGの機械的検査(要素数・タイトル抽出)は実施。人手の視認確認は本実行では不可。"},
  {"name": "geometry_inspection", "status": "unavailable", "basis": "描画後の実寸計測手段なし。近似推定のみで判定しない規則に従い実施せず。"},
  {"name": "interactive_edit", "status": "unavailable", "basis": "draw.ioアプリなし。移動追従テスト不可。"},
  {"name": "print_review", "status": "unavailable", "basis": "PDF変換ライブラリ不在・印刷プレビュー手段なし。"}
 ],
 "selected_font": {"family": "Meiryo", "basis": "drawio標準UIフォント相当。SVG生成時にfontFamily=Meiryoを指定。", "availability": "available"},
 "selected_design": {
  "layout": "left_to_right",
  "node_style": "rounded=1, whiteSpace=wrap",
  "edge_style": "orthogonalEdgeStyle, rounded",
  "palette": {"sheet": "#DAE8FC", "file": "#D5E8D4", "documented_entity": "#FFE6CC", "figure": "#E1D5E7", "edge": "#426A91", "warn": "#A56A12", "conflict": "#B33A3A"}
 },
 "measurement_profiles": [],
 "targets": [
  {"target_id": "T-PG-01", "kind": "page", "ref": "PG-01"},
  {"target_id": "T-PG-02", "kind": "page", "ref": "PG-02"},
  {"target_id": "T-PG-03", "kind": "page", "ref": "PG-03"},
  {"target_id": "T-PG-04", "kind": "page", "ref": "PG-04"},
  {"target_id": "T-LEDGER-SOURCE", "kind": "artifact", "ref": "art-source"},
  {"target_id": "T-LEDGER-EVIDENCE", "kind": "artifact", "ref": "art-evidence"},
  {"target_id": "T-LEDGER-GRAPH", "kind": "artifact", "ref": "art-graph"},
  {"target_id": "T-LEDGER-ISSUES", "kind": "artifact", "ref": "art-issues"},
  {"target_id": "T-DIAGRAM", "kind": "artifact", "ref": "art-diagram"},
  {"target_id": "T-PREVIEW-P1", "kind": "artifact", "ref": "art-preview-p1"},
  {"target_id": "T-PREVIEW-P2", "kind": "artifact", "ref": "art-preview-p2"},
  {"target_id": "T-PREVIEW-P3", "kind": "artifact", "ref": "art-preview-p3"},
  {"target_id": "T-PREVIEW-P4", "kind": "artifact", "ref": "art-preview-p4"},
  {"target_id": "T-USAGE", "kind": "artifact", "ref": "art-usage"},
  {"target_id": "T-MANIFEST", "kind": "artifact", "ref": "art-manifest"}
 ],
 "expected_checks": [],
 "results": [],
 "result_history": [],
 "exceptions": [],
 "graph_summary": {"count": 23, "note": "関係23件のうち個別コネクタ8本。残り15関係はレイアウト・注記で表現(implied_by_layout)。EDG-REL-23は注記ラベル。"},
 "preview_summary": {"count": 4, "formats": ["svg"], "note": "preview_p1..p4.svg。ネイティブ図と同一版(R1)から生成。"},
 "artifact_inventory": [],
 "summary": {},
 "final_status": "verification_incomplete"
}

checks = [
 ("configuration", ["config_types","config_resolution","config_safety"], "T-MANIFEST"),
 ("content_traceability", ["evidence_trace","inspection_consistency","claim_separation","presentation_safety","coverage_trace"], "T-LEDGER-GRAPH"),
 ("record_integrity", ["record_schema","record_references","graph_mapping","acquisition_state"], "T-LEDGER-GRAPH"),
 ("native_structure", ["native_parse","native_editability","native_references"], "T-DIAGRAM"),
 ("geometry", ["shape_overlap","line_penetration","line_overlap","label_collision","endpoint_alignment","layout_balance"], "T-DIAGRAM"),
 ("saved_file_reopen", ["actual_reopen","reopen_display","reopen_editability"], "T-DIAGRAM"),
 ("visual_review", ["visual_overview","visual_normal","visual_detail","visual_completeness"], "T-DIAGRAM"),
 ("connection_follow", ["follow_behavior","follow_coverage","copy_isolation"], "T-DIAGRAM"),
 ("print_readability", ["print_text","print_bounds","print_method"], "T-DIAGRAM"),
 ("preview_consistency", ["preview_revision","preview_pages"], "T-PREVIEW-P1"),
 ("artifact_completeness", ["artifact_presence","artifact_format","artifact_contents","artifact_revision","artifact_request_status","report_consistency"], "T-MANIFEST"),
]
for cid, criteria, tgt in checks:
    for crid in criteria:
        report["expected_checks"].append({"check_id": cid, "criterion_id": crid, "target_id": tgt})

results = []
for ec in report["expected_checks"]:
    cid, crid = ec["check_id"], ec["criterion_id"]
    r = {"check_id": cid, "criterion_id": crid, "target_id": ec["target_id"], "delivery_revision": REV, "status": None, "method": None, "record": None}
    if cid == "configuration":
        r["status"] = "PASS"; r["method"] = "AI自動検査(Python)"
        r["record"] = "台帳4件の型・必須項目・schema_version一致・run_id/delivery_revision一致を確認。"
    elif cid == "content_traceability":
        r["status"] = "PASS"; r["method"] = "AI自動検査(参照整合監査)"
        r["record"] = "EV27・OBJ14・REL23・ISS7の参照が全件解決(監査スクリプト、エラー0)。coverage_decisions CV-01..05で掲載/要約/省略/未確認を追跡。"
    elif cid == "record_integrity":
        r["status"] = "PASS"; r["method"] = "AI自動検査(参照整合監査)"
        r["record"] = "ID一意・参照解決・graph_mapping(インスタンス56/コネクタ台帳23/ネイティブID一致)を確認。"
    elif cid == "native_structure":
        r["status"] = "PASS"; r["method"] = "AI自動検査(XML解析)"
        r["record"] = "4ページ解析成功・頂点64・コネクタ20(参照全解決・凡例サンプル1本は意図的な浮き線)・ページID=PG-01..04・台帳のnative_cell_idと一致。"
    elif cid == "geometry":
        r["status"] = "BLOCKED"
        r["record"] = "機能不足(geometry_inspection unavailable)。近似推定のみでの0件主張は禁止規則により実施せず。"
    elif cid == "saved_file_reopen":
        r["status"] = "BLOCKED"
        r["record"] = "draw.io desktop不在。drawio2svgでの再解析は実施したが、アプリ再読込の表示確認は未実施。"
    elif cid == "visual_review":
        r["status"] = "BLOCKED"
        r["record"] = "rendererは利用可能だが人手視認(visual_review)不可。機械的抽出(タイトル・要素数)までは実施済み。"
    elif cid == "connection_follow":
        r["status"] = "BLOCKED"
        r["record"] = "interactive_edit不可(アプリなし)。接続線>0確定済みのためNAは不可。"
    elif cid == "print_readability":
        r["status"] = "NA"
        r["record"] = "print_review_required=false を設定で確定(条件false立証済み)。印刷確認用出力は未生成。"
    elif cid == "preview_consistency":
        r["status"] = "PASS"; r["method"] = "AI自動検査(SVG生成ログ・要素数抽出)"
        r["record"] = "preview_p1..p4.svg が同一版R1のネイティブ図から生成成功。ページ数4の一致と各ページのタイトル・図形抽出を確認。"
    elif cid == "artifact_completeness":
        r["status"] = "PASS"; r["method"] = "AI自動検査(ファイル存在・JSON/YAML解析)"
        r["record"] = "必須8成果物+プレビュー4を生成・登録。request_status に未生成なし。"
    results.append(r)

report["results"] = results
sc = {"PASS": 0, "FAIL": 0, "BLOCKED": 0, "NOT_RUN": 0, "NA": 0}
for r in results:
    sc[r["status"]] += 1
report["summary"] = {
 "expected_count": len(report["expected_checks"]),
 "result_count": len(results),
 "status_counts": sc,
 "required_artifact_count": 8,
 "required_artifact_satisfied_count": 8,
 "optional_output_unavailable_count": 0,
 "invalid_result_count": 0,
 "stale_result_count": 0,
 "limitations": report["limitations"]
}
json.dump(report, open('validation_report.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('validation_report.json written. status_counts:', sc)
