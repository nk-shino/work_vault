"""内部値（英語）と日本語表示の対応。画面のテンプレートと CSV 出力で共通に使う。

web 層からも domain 層からも参照できるよう、ラベルの一覧はここに置く。
対応するキーの無い値はそのまま出す（未知の内部値を黙って空文字にしないため）。
"""

LABELS = {
    "draft": "草案",
    "active": "有効",
    "disputed": "係争中",
    "archived": "アーカイブ済み",
    "ai_draft": "AI草案",
    "needs_review": "要レビュー",
    "confirmed": "確定",
    "rejected": "却下",
    "pending": "未処理",
    "accepted": "採用済み",
    "related": "関連",
    "synonym": "同義",
    "abbrev_of": "略語の元",
    "has_abbrev": "略語",
    "broader": "上位概念",
    "narrower": "下位概念",
    "confused_with": "混同注意",
    "sense": "語義",
    "relation": "関係",
    "evidence": "用例の追加",
    "term": "用語",
    "auto": "自動採用",
    "correct": "正しい",
    "needs_fix": "修正が必要",
    "unsure": "判断できない",
    "useful": "役に立つ",
    "not_useful": "役に立たない",
}
