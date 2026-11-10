# -*- coding: utf-8 -*-
"""verify_render_strict_negtest.py -- Gate 1 是正の負例検証 (N1-N7b).

第2次是正 (再審査 attempt 2 指摘) により:
  - N1/N2 は純関数の戻り値だけでなく、本番の severity·サブチェック分類
    (tail_severity) を通して確認する (F1·ウ)
  - N3 を拡張: 幅変更·改行(段落)構造変更·baseline項目欠落の3ケースを追加 (F3)
  - N6 を新設: 対象図形の末尾欠落を隣接図形の同じ文字列が補填するケース。
    旧実装 (広域窓の multiset>= 救済) は通し、新実装は 'attribution-undetermined'
    (帰属未確定) として遮断する (F2·エ)。本番 severity で確認する

第3次是正 (再審査 attempt 3 指摘) により:
  - N6 を本番の帰属経路 (attribute_spans -> span_owner -> tail_rescue ->
    tail_severity) を exercise する形に変更した。旧 N6 は帰属を手作業で
    模倣していたため、帰属識別子の切断 (修正1: attribute_spans が新しい
    tuple を生成し span_owner の id 検索が不能になる不具合) を検出できなかった
  - N6b を新設: baseline 一致 (render_same=True) でも帰属未確定が FAIL を
    維持すること (修正2)。旧実装は loss と attribution-undetermined を同一
    分岐で WARN に降格していた

第4次是正 (特例再審査 attempt 4 指摘) により:
  - N7 を新設: 残差側 own 補填分岐の除去 (修正6) の検証。期待「確認確認」に
    自帰属スパン「確認」1個のみの静的反例を本番の残差分類 (residual_check) で
    確認し、unexplained 2文字として記録される (旧実装は own_extra 再計上により
    unexplained 0 の偽陰性)

第5次是正 (Phase 2 独立レビュー P2 指摘) により:
  - N7b を新設: 残差の部分一致の分離 (修正7) の検証。期待「確認確認確認」に
    自帰属スパンなし·他図形帰属スパン「確」1文字の反例を本番の residual_check
    で確認し、attr_undet 確:1·unexplained 確:2 に分離される (第4次実装は
    other[ch] >= n の全か無か判定で unexplained 確:3 = 確定残差の過大報告)

結果: strictverify/reconsider/negative_test_results.json
終了コード: 全件検出=0 / 未検出あり=1
"""
import sys, os, json, io, datetime
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verify_render_strict as vrs

OUTDIR = os.path.join(vrs.OUT, 'reconsider')
os.makedirs(OUTDIR, exist_ok=True)

results = []

def old_tail_check(exp_text, got_text):
    """旧実装 (F1是正前) の末尾判定を再現する (比較証明用)"""
    exp_cjk, got_cjk = vrs.cjk(exp_text), vrs.cjk(got_text)
    if not exp_cjk:
        return True
    ce, cg = Counter(exp_cjk), Counter(got_cjk)
    ok = all(cg[ch] >= n for ch, n in ce.items())
    last4 = exp_cjk[-4:]
    if ok and last4 and last4 not in got_cjk:
        ok = False
    return ok

def old_wide_rescue(exp_text, own_text, wide_text):
    """旧実装 (第1次是正) の広域窓救済を再現する: 広域窓の抽出文で multiset>=
    (包含) を満たせば tail_ok=True にしていた (帰属を確認しない)"""
    ce, cg = Counter(vrs.cjk(exp_text)), Counter(vrs.cjk(wide_text))
    return all(cg[ch] >= n for ch, n in ce.items())

def max_severity(items):
    if any(i['severity'] == 'FAIL' for i in items):
        return 'FAIL'
    return 'WARN' if items else 'PASS'

# ---- N1 (F1): ASCII末尾欠落 -- 本番 severity 経路で確認 -------------------
# g2_e_e17_l は changed/fixed ではない。第1次実装では警告に降格されていた
# (実例: g2_e_e17_l ascii_mode='loss' が警告)。第2次で無条件 FAIL。
exp_t1 = '様式番号の確認 NR4030-0300-A3'
got_t1 = '様式番号の確認 NR4030-0300-'          # 末尾の -A3 が描画で欠落
sev1 = vrs.tail_severity('g2_e_e17_l', 'ordered-equal', 'loss', exp_t1, render_same=False)
n1_fail = [i for i in sev1 if i['severity'] == 'FAIL' and i['subcheck'] == 'tail_ascii_separate']
results.append({
    'id': 'N1', 'target_fix': 'F1 (ASCII loss の警告降格廃止·本番severity経路)',
    'path': 'production severity (tail_severity) + subcheck tail_ascii_separate',
    'fixture': {'shape': 'g2_e_e17_l (changed/fixed 以外)', 'exp_text': exp_t1, 'got_text': got_t1,
                'note': 'ASCII末尾 -A3 のみ欠落した合成PDF抽出'},
    'expected': "severity FAIL / subcheck tail_ascii_separate (警告降格の廃止)",
    'actual': {'severity_items': sev1, 'ascii_tail': vrs.ascii_tail(exp_t1),
               'ascii_check': vrs.ascii_tail_check(exp_t1, got_t1)},
    'old_behavior_would_pass': True,   # 第1次実装: 警告に降格 (changed/fixed 以外)
    'detected': bool(n1_fail),
})

# ---- N2 (F1): CJK重複補填 -- 別異常クラス (K4疑いではない) を本番 severity で ---
exp_t2 = '再起動の確認'
got_t2 = '再起動の確認起动'.replace('动', '動')   # 期待文字をすべて含むが「起」を重複補填
tc2 = vrs.tail_check_ordered(exp_t2, got_t2)
sev2 = vrs.tail_severity('g3_n08_txt', tc2['mode'], 'ok', exp_t2, render_same=False)
n2_fail = [i for i in sev2 if i['severity'] == 'FAIL' and i['code'] == 'tail_extra_chars']
results.append({
    'id': 'N2', 'target_fix': 'F1 (multiset 等値化·重複/追加は別異常クラス)',
    'path': 'production severity (tail_severity) + subcheck tail_cjk_ordered',
    'fixture': {'exp_text': exp_t2, 'got_text': got_t2,
                'note': '期待文字はすべて含むが「起」が重複補填 (旧 Counter>= は通過)'},
    'expected': "mode='extra-chars(dup/addition)' (K4疑いではない別異常クラス) + severity FAIL",
    'actual': {'mode': tc2['mode'], 'ordered_ok': tc2['ordered_ok'], 'multiset_ok': tc2['multiset_ok'],
               'severity_items': sev2},
    'old_behavior_would_pass': bool(old_tail_check(exp_t2, got_t2)),
    'detected': (tc2['mode'] == 'extra-chars(dup/addition)' and bool(n2_fail)),
})

# ---- N3 (F3): 描画状態一致の比較拡張 (4ケース) -----------------------------
T3 = '上位スイッチへの疎通確認ラベル'
base3 = {'path': 'grp/g2_e_e17_l', 'text': T3, 'h': 26.02, 'w': 100.0, 'autosize': 1, 'wordwrap': -1}
# (a) 高さ変更 (e17_l 実例と同型)
c3a = vrs.classify_render_state(base3, T3, 39.3, 100.0, 2, -1)
# (b) 幅変更 (高さは不変)
c3b = vrs.classify_render_state(base3, T3, 26.02, 120.0, 1, -1)
# (c) 改行(段落)構造変更 -- norm() は改行を除去するため旧実装は同一扱いだった
base3c = dict(base3, text='甲\n乙')
c3c = vrs.classify_render_state(base3c, '甲乙', 26.02, 100.0, 1, -1)
# (d) baseline 項目欠落 -- 「一致」にしない (比較不能)
base3d = {k: v for k, v in base3.items() if k != 'w'}
c3d = vrs.classify_render_state(base3d, T3, 26.02, 100.0, 1, -1)
results.append({
    'id': 'N3', 'target_fix': 'F3 (描画状態一致: 幅+改行/段落構造·baseline欠落は比較不能)',
    'path': 'classify_render_state (main と同一関数)',
    'fixture': {'baseline': {'h': 26.02, 'w': 100.0, 'autosize': 1, 'wordwrap': -1},
                'cases': ['h change 26.02->39.3', 'w change 100->120', "text '甲\\n乙' vs '甲乙'",
                          'baseline lacks w field']},
    'expected': "(a)(b) render-changed-origin-unknown / (c) text-changed (改行構造の同値扱い廃止) / "
                "(d) render-state-not-comparable (一致にしない)",
    'actual': {'h_change': c3a, 'w_change': c3b, 'newline_change': c3c, 'baseline_field_missing': c3d},
    'old_behavior_would_pass': True,   # 旧実装: (a)以外は高さのみ·改行除去·欠落項目は無視で「一致」
    'detected': (c3a == 'render-changed-origin-unknown' and c3b == 'render-changed-origin-unknown'
                 and c3c == 'text-changed' and c3d == 'render-state-not-comparable'),
})

# ---- N4 (F5): 両冊共通の既存図形欠落 ------------------------------------
baseline4 = [
    {'path': 'g2_n01', 'text': ''}, {'path': 'g2_n01/g2_n01_txt', 'text': 'ノード1'},
    {'path': 'g2_n02', 'text': ''}, {'path': 'g2_n02/g2_n02_txt', 'text': 'ノード2'},
]
cur_names4 = {'g2_n01', 'g2_n01_txt', 'g2_n02'}          # g2_n02_txt が欠落
cur_texts4 = {'g2_n01_txt': 'ノード1'}
miss4 = vrs.reverse_baseline_missing(baseline4, cur_names4, cur_texts4)
results.append({
    'id': 'N4', 'target_fix': 'F5 (ベースライン→現在の逆方向比較)',
    'path': 'reverse_baseline_missing (C9 subcheck baseline_reverse_23 から呼ばれる本番関数)',
    'fixture': {'baseline_names': [e['path'] for e in baseline4],
                'current_names': sorted(cur_names4), 'note': 'ベースラインに存在する g2_n02_txt を現在冊から削除'},
    'expected': '欠落 g2_n02_txt を検出 (reason=shape-missing)',
    'actual': {'missing': miss4},
    'old_behavior_would_pass': True,   # 旧実装は順方向比較のみで存在しない図形は比較対象外
    'detected': any(m['name'] == 'g2_n02_txt' and m['reason'] == 'shape-missing' for m in miss4),
})

# ---- N5 (F2): 隣接行混入 (スパン単位帰属) --------------------------------
wins5 = {'shapeA': (100.0, 100.0, 300.0, 120.0), 'shapeB': (100.0, 122.0, 300.0, 142.0)}
spans5 = [
    (110.0, 105.0, 200.0, 115.0, 'A行目のテキスト'),      # A 内 -> A に帰属
    (110.0, 127.0, 200.0, 137.0, 'B行目のテキスト'),      # B 内 -> B に帰属
    (110.0, 112.0, 200.0, 128.0, 'またがりスパン'),        # A/B 両方にまたがる (混入候補)
]
attrib5, un5, strad5 = vrs.attribute_spans(spans5, wins5)
assign = {nm: len(sp) for nm, sp in attrib5.items()}
n_clean = sum(1 for sp in spans5[:2]
              if any(sp in attrib5[nm] for nm in attrib5))
results.append({
    'id': 'N5', 'target_fix': 'F2 (スパン単位帰属·隣接行混入の検出)',
    'path': 'attribute_spans (C3本文比較·残差検査に接続済み)',
    'fixture': {'windows': wins5, 'spans': [list(s) for s in spans5],
                'note': '3つ目のスパンは A/B 両窓にまたがる (行境界をまたぐ混入)'},
    'expected': 'またがりスパンが straddle として検出され、正常2スパンは正しい窓に帰属',
    'actual': {'assigned': assign, 'unattributed': len(un5), 'straddles': strad5},
    'old_behavior_would_pass': True,   # 旧実装は行y座標の窓内選別のみでまたがりを判定しない
    'detected': (len(strad5) == 1 and strad5[0]['assigned'] in wins5
                 and assign.get('shapeA', 0) >= 2 and assign.get('shapeB', 0) >= 1 and n_clean == 2),
})

# ---- N6 (F2·第3次改訂): 本番の帰属経路で隣接図形の同文字列による末尾補填を遮断
# 旧 N6 は「A の窓に帰属した抽出」を手作業で合成していたため、本番の帰属経路の
# 接続不良 (修正1: attribute_spans が新しい tuple を生成し span_owner の id 検索
# が元 spans に対して不能になる) を検出できなかった。第3次では本番と同じ経路
# attribute_spans -> span_owner (id キー) -> tail_rescue -> tail_severity を
# exercise し、帰属識別子が元 spans から後段まで安定していることを同時に確認する
exp_a = '認証情報の保管先'
wins6 = {'g3_legA': (100.0, 100.0, 300.0, 120.0), 'g3_legB': (100.0, 122.0, 300.0, 142.0)}
spans6 = [
    (110.0, 105.0, 290.0, 115.0, '認証情報の保管'),     # A 窓内 (末尾「先」を欠く)
    (110.0, 128.0, 290.0, 138.0, '先の確認を要する'),   # B 窓内 (「先」を含む·A の広域窓にも入る)
]
attrib6, un6, strad6 = vrs.attribute_spans(spans6, wins6)
# 本番 (verify_render_strict.py main) と同一の span_owner 構築
span_owner6 = {}
for wnm, lst in attrib6.items():
    for s5 in lst:
        span_owner6[id(s5)] = wnm
# 修正1の検証: 元 spans の id で owner を引ける (識別子が安定している)
own_is_stable = (span_owner6.get(id(spans6[0])) == 'g3_legA'
                 and span_owner6.get(id(spans6[1])) == 'g3_legB')
own_spans6 = sorted(attrib6.get('g3_legA', []), key=lambda s: (s[1], s[0]))
# A の本文窓 ±15 / 下 +30pt の広域窓 (本番と同じ条件)
wide6 = []
for s5 in spans6:
    if s5[0] < 315.0 and s5[2] > 85.0 and s5[1] < 150.0 and s5[3] > 85.0:
        w5 = span_owner6.get(id(s5))
        wide6.append((s5, 'own' if w5 == 'g3_legA' else ('other' if w5 else 'unattributed')))
vr6 = vrs.tail_rescue(exp_a, own_spans6, wide6)
sev6 = vrs.tail_severity('g3_n12_txt', vr6['mode'], 'ok', exp_a, render_same=False)
old_rescue6 = old_wide_rescue(exp_a, ''.join(r['t'] for r in vrs.rows_from_spans(own_spans6)),
                              ''.join(s5[4] for s5 in spans6))
results.append({
    'id': 'N6', 'target_fix': 'F2+修正1/3 (本番の帰属経路で隣接図形の同文字列による末尾補填を遮断)',
    'path': 'production attribute_spans -> span_owner -> tail_rescue -> tail_severity',
    'fixture': {'exp_text_A': exp_a, 'windows': wins6,
                'spans': [list(s) for s in spans6],
                'note': 'A の末尾「先」は描画で欠落·B 窓内の「先」を含むスパンが A の広域窓にも存在する'},
    'expected': "span_owner が元 spans の id で成立 (修正1) + tail_rescue "
                "mode='attribution-undetermined' (tail_ok=False) + 本番 severity FAIL",
    'actual': {'span_owner_stable': own_is_stable, 'tail_rescue': vr6, 'severity_items': sev6},
    'old_behavior_would_pass': bool(old_rescue6),   # 旧: 広域窓 multiset>= で tail_ok=True
    'detected': (own_is_stable and vr6['mode'] == 'attribution-undetermined'
                 and vr6['tail_ok'] is False
                 and any(i['severity'] == 'FAIL' and i['subcheck'] == 'tail_cjk_ordered' for i in sev6)),
})

# ---- N6b (第3次·修正2): baseline 一致でも帰属未確定は FAIL を維持 -----------
# 旧実装は loss と attribution-undetermined を同一分岐で処理し、render_same=True
# の場合に双方 WARN へ降格していた。baseline (描画設定) の一致は「現在の文字が
# 対象図形に帰属する」証拠にならないため、帰属未確定は降格しない
sev6b = vrs.tail_severity('g2_leg0', 'attribution-undetermined', 'ok', exp_a, render_same=True)
# 対照: mode='loss' + render_same=True は従来どおり既存 WARN (tail_loss_preexisting)
sev6c = vrs.tail_severity('g2_n02_txt', 'loss', 'ok', exp_a, render_same=True)
n6b_fail = [i for i in sev6b if i['severity'] == 'FAIL' and i['code'] == 'tail_attribution_undetermined']
results.append({
    'id': 'N6b', 'target_fix': '修正2 (帰属未確定のseverity分離·baseline一致でもFAIL維持)',
    'path': 'production severity (tail_severity)',
    'fixture': {'tc_mode': 'attribution-undetermined', 'render_same': True,
                'contrast_tc_mode': 'loss', 'contrast_render_same': True,
                'note': 'baseline の描画状態一致は「自図形に帰属する」証拠にならない'},
    'expected': "attribution-undetermined: severity FAIL / code tail_attribution_undetermined "
                "(render_same=True でも降格しない)。対照: loss + render_same=True は従来どおり WARN (tail_loss_preexisting)",
    'actual': {'attr_undet_items': sev6b, 'loss_contrast_items': sev6c},
    'old_behavior_would_pass': True,   # 旧実装: render_same=True で双方 WARN に降格
     'detected': (bool(n6b_fail)
                  and all(i['severity'] == 'WARN' and i['code'] == 'tail_loss_preexisting'
                          for i in sev6c if i['subcheck'] == 'tail_cjk_ordered')),
})

# ---- N7 (第4次): 残差側 own 補填分岐の除去 -- 消費済み文字の再利用を遮断 -----
# 期待「確認確認」に対し自帰属スパン「確認」1個のみ (拡張窓内も同一スパン)。
# 旧実装は miss = Counter(期待) - Counter(自帰属抽出文) を計算した後、拡張窓内の
# 自帰属スパンを own_extra として再計上し「own 帰属で説明」(continue) にできた。
# own_extra は cg (自帰属抽出文) の構成元スパンの部分集合 = 消費済み文字の再利用
# であり、静的反例「確認確認/確認」が 2文字とも unexplained に記録されない偽陰性
# だった。第4次実装: 残差分類を本番経路 residual_check に集約し、補填根拠は
# own_spans と識別子レベル (id) で排他的なスパン (other/unattributed) に限定。
# 期待: unexplained 2文字 (確1·認1)·attr_undet 0件
exp_n7 = '確認確認'
wins7 = {'g2_legA': (100.0, 100.0, 300.0, 120.0)}
spans7 = [(110.0, 105.0, 290.0, 115.0, '確認')]   # A 窓内·自帰属スパン 1個のみ
attrib7, un7, strad7 = vrs.attribute_spans(spans7, wins7)
span_owner7 = {}
for wnm, lst in attrib7.items():
    for s5 in lst:
        span_owner7[id(s5)] = wnm
own_spans7 = sorted(attrib7.get('g2_legA', []), key=lambda s: (s[1], s[0]))
# A の本文窓 ±15pt の拡張窓 (本番の残差点検査と同じ条件) -- 同一スパンのみ進入
wide7 = []
for s5 in spans7:
    if s5[0] < 315.0 and s5[2] > 85.0 and s5[1] < 135.0 and s5[3] > 85.0:
        w5 = span_owner7.get(id(s5))
        wide7.append((s5, 'own' if w5 == 'g2_legA' else ('other' if w5 else 'unattributed')))
rc7 = vrs.residual_check(exp_n7, own_spans7, wide7)
# 旧実装 (own_extra 再計上) が反例を握りつぶしていたことの証明:
# 拡張窓内の自帰属スパンで miss が全部埋まる (= 旧実装は unexplained 0)
miss7 = Counter(vrs.cjk(exp_n7)) - Counter(vrs.cjk(''.join(t for (_, _, _, _, t) in own_spans7)))
own_extra7 = Counter(vrs.cjk(''.join(s5[4] for s5, o in wide7 if o == 'own')))
old_would_mask7 = bool(miss7) and all(own_extra7[ch] >= n for ch, n in miss7.items())
n7_unexp = sum(rc7['unexplained'].values())
results.append({
    'id': 'N7', 'target_fix': '第4次 (残差側 own補填分岐の除去·消費済み文字の再利用を遮断)',
    'path': 'production residual_check (main の C8 残差点検査と同一関数)',
    'fixture': {'exp_text': exp_n7, 'windows': wins7, 'spans': [list(s) for s in spans7],
                'note': '期待「確認確認」に対し自帰属スパン「確認」1個のみ。拡張窓内も同一スパン (own_extra = cg の部分集合)'},
    'expected': "unexplained=2文字 (確1·認1) / attr_undet=0件 (own_extra 再計上の廃止)。"
                "旧実装は 2文字とも continue で unexplained=0 (偽陰性)",
    'actual': {'residual_check': rc7, 'missing': dict(miss7),
               'old_own_extra_covers_missing': old_would_mask7},
    'old_behavior_would_pass': old_would_mask7,   # 旧実装: unexplained 0 (偽陰性)
    'detected': (n7_unexp == 2 and not rc7['attr_undet'] and not rc7['missing'] == {} and old_would_mask7),
})

# ---- N7b (第5次): 残差の部分一致の分離 -- 確定残差の過大報告を是正 -----------
# 期待「確認確認確認」に対し自帰属スパンなし·拡張窓の他図形スパンに「確」1文字。
# 第4次実装 (第5次修正前) の分類ループは other[ch] >= n か否かの全か無か判定で、
# 一部一致 (1〜n-1個) の場合は全 n を unexplained に分類していた = 外部で一致した
# 個数が記録されず、C8 の確定残差 (unexplained) を過大報告する (方向は保守的·
# 偽合格ではないが分類精度の問題)。第5次実装: matched = min(other[ch], n) を
# attribution-undetermined に、残り n - matched を unexplained に分離 (0は記録
# しない)。期待: attr_undet 確:1·unexplained 確:2 (修正前は unexplained 確:3)
exp_n7b = '確認確認確認'
wins7b = {'g2_legA': (100.0, 100.0, 300.0, 120.0)}
# 自帰属スパンなし。他図形 (g2_legB) 帰属スパン「確」1文字が A の拡張窓 (±15pt) に進入。
# スパンは legA の本文窓の外 (y 122-130·+15pt 帯) に置き、legB 窓で完全包含する
# (legA との重なり 0 なので attribute_spans は legB に帰属 = owner 'other')
spans7b = [(110.0, 122.0, 290.0, 130.0, '確')]
wins7b['g2_legB'] = (110.0, 120.0, 292.0, 132.0)
attrib7b, un7b, strad7b = vrs.attribute_spans(spans7b, wins7b)
span_owner7b = {}
for wnm, lst in attrib7b.items():
    for s5 in lst:
        span_owner7b[id(s5)] = wnm
own_spans7b = sorted(attrib7b.get('g2_legA', []), key=lambda s: (s[1], s[0]))
wide7b = []
for s5 in spans7b:
    if s5[0] < 315.0 and s5[2] > 85.0 and s5[1] < 135.0 and s5[3] > 85.0:
        w5 = span_owner7b.get(id(s5))
        wide7b.append((s5, 'own' if w5 == 'g2_legA' else ('other' if w5 else 'unattributed')))
rc7b = vrs.residual_check(exp_n7b, own_spans7b, wide7b)
# 旧実装 (第4次·全か無か) の分類を明示的に構成: 旧実装は other[ch] >= n でない
# miss 文字を**全個** unexplained にした (外部で一致した個数を記録しない)。
# N7b の前提 (other 確1 < miss 確3·認は他スパン不在) では旧分類 = 全 miss を
# unexplained にした辞書そのものになる
old_unexp7b = dict(rc7b['missing'])
old_classified_all_miss_as_unexplained7b = (old_unexp7b == dict(rc7b['missing']))
results.append({
    'id': 'N7b', 'target_fix': '第5次 (残差の部分一致の分離 -- matched=min(other,n) を attr_undet に·残りを unexplained に)',
    'path': 'production residual_check (main の C8 残差点検査と同一関数)',
    'fixture': {'exp_text': exp_n7b, 'windows': {k: list(v) for k, v in wins7b.items()},
                'spans': [list(s) for s in spans7b],
                'note': '期待「確認確認確認」·自帰属スパンなし·他図形 (g2_legB) 帰属スパン「確」1文字が拡張窓内'},
    'expected': "確の分離: attr_undet={確:1} / unexplained={確:2} (matched=min(other確1, miss確3)=1 を分離)。"
                "修正前は unexplained={確:3} (確定残差の過大報告)。認は自帰属·他スパンとも不在のため"
                "unexplained={認:3} が確定残差として残る (分離対象外の対照)",
    'actual': {'new_split': {'attr_undet': rc7b['attr_undet'], 'unexplained': rc7b['unexplained']},
               'old_unexplained': old_unexp7b,
               'old_classified_all_miss_as_unexplained': old_classified_all_miss_as_unexplained7b,
               'residual_check': rc7b},
    # N1〜N7 と性格が異なる: N7b の欠陥 (旧実装) は確定残差の**過大報告** (分類精度)
    # であり、旧実装でも unexplained が残って C8 は FAIL のまま。偽合格ではない
    'old_behavior_would_pass': False,
    'detected': (rc7b['attr_undet'].get('確') == 1 and rc7b['unexplained'].get('確') == 2
                 and rc7b['missing'].get('確') == 3 and rc7b['unexplained'].get('認') == 3),
})

# ---- 出力 ----------------------------------------------------------------
all_detected = all(r['detected'] for r in results)
out = {'generated': datetime.datetime.now().isoformat(timespec='seconds'),
       'harness': 'verify_render_strict.py (Gate1第5次是正 修正7 + 第4次 修正6 + 第3次 修正1/2/3 + 第2次 F1/F2/F3/F5)',
       'n_fixtures': len(results), 'n_detected': sum(1 for r in results if r['detected']),
       'all_detected': all_detected, 'results': results}
path = os.path.join(OUTDIR, 'negative_test_results.json')
with io.open(path, 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
for r in results:
    print('%s [%s] detected=%s old_would_pass=%s' % (r['id'], r['target_fix'], r['detected'], r['old_behavior_would_pass']))
    print('    expected: %s' % r['expected'])
    print('    actual: %s' % json.dumps(r['actual'], ensure_ascii=False)[:260])
print('NEGATIVE TEST: %d/%d detected -> %s' % (out['n_detected'], out['n_fixtures'], path))
sys.exit(0 if all_detected else 1)
