"""動作確認用の架空メール 50 通を fixtures/mails/ に作る。

実在しそうな社内用語・人名・製品名を避けるため、舞台は「浮遊島の竜舎」という明らかな作り話にする。
乱数の種を固定しているので、何度実行しても同じファイルができる。
マスキングの確認用に、架空のメールアドレス・電話番号・URL・金額・シリアル番号も混ぜる
（ドメインは RFC 2606 で予約された example.invalid、電話番号は 000 始まり）。
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import format_datetime
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "fixtures" / "mails"
JST = timezone(timedelta(hours=9))

PEOPLE = [
    ("竜乃 空太", "sora.tatsuno"),
    ("雲居 ほし", "hoshi.kumoi"),
    ("霧島 ぽぽ", "popo.kirishima"),
    ("星見 もくれん", "mokuren.hoshimi"),
    ("羽根田 ふわり", "fuwari.haneda"),
]

# スレッドの話題ごとに、一緒に出てくる語を決めておく（共起の確認用）
TOPICS = [
    {
        "subject": "竜舎の卵温計の交換について",
        "lines": [
            "竜舎の卵温計が夜間に低めの値を示しています。",
            "卵温計は孵化室の温度を測る道具で、竜舎ごとに2台ずつ置いています。",
            "竜舎の東棟だけ卵温計の校正がずれているようです。",
            "交換用の卵温計は{money}で見積もりが来ています。シリアルは{serial}です。",
        ],
    },
    {
        "subject": "浮遊石のFLT点検の日程",
        "lines": [
            "来週は浮遊石のFLT点検の週です。",
            "FLT点検では浮遊石の浮力が規定値に入っているかを確かめます。",
            "浮遊石が沈み始めたらFLT点検を前倒ししてください。",
            "点検手順は {url} にあります。仕様の変更点も同じ場所です。",
        ],
    },
    {
        "subject": "ほうき便とスカイポストの使い分け",
        "lines": [
            "急ぎの部品はほうき便で、書類はスカイポストで送ってください。",
            "ほうき便は午前便と午後便があり、スカイポストは翌日着です。",
            "ほうき便の料金が{money}に改定されました。",
            "スカイポストの窓口は {phone} です。",
        ],
    },
    {
        "subject": "星読み台帳のMGK記録",
        "lines": [
            "星読み台帳にMGKの結果を記入してください。",
            "MGKは魔導ゲージ校正の略で、月に一度、星読み台帳に残します。",
            "星読み台帳の書式が変わったので、MGKの欄の位置に注意してください。",
            "星読み台帳の原本は事務棟にあります。問い合わせは {email} へ。",
        ],
    },
    {
        "subject": "竜車の手配（竜舎とお間違えなく）",
        "lines": [
            "竜車は荷物を運ぶ乗り物で、竜舎は竜を飼う建物です。",
            "竜車の予約は前日までにお願いします。ほうき便に載らない大きな荷物は竜車で運びます。",
            "竜車と竜舎は読みが同じなので、発注書では必ず漢字を確認してください。",
            "竜車の車輪は{serial}の部品と交換済みです。",
        ],
    },
    {
        "subject": "霧抜き作業と雲切りの順番",
        "lines": [
            "霧抜き作業の前に雲切りを済ませてください。",
            "雲切りは島の周りの雲を払う作業で、霧抜き作業は竜舎の中の湿気を抜く作業です。",
            "雲切りが遅れると霧抜き作業も後ろにずれます。",
            "霧抜き作業の担当表を更新しました。",
        ],
    },
    {
        "subject": "ドラゴンミルクの出荷量",
        "lines": [
            "今月のドラゴンミルクの出荷量は先月と同程度です。",
            "ドラゴンミルクは竜舎で毎朝集めて、ほうき便で出荷しています。",
            "ドラゴンミルクの単価は{money}のままです。",
        ],
    },
]

OPENINGS = ["お疲れ様です。", "いつもお世話になっております。"]
CLOSINGS = ["よろしくお願いいたします。", "以上です。"]
DISCLAIMER = (
    "このメールは架空の検証用データです。誤って届いた場合は破棄してください。"
    "本メールには機密情報は含まれていません。"
)


def fill(line: str, rng: random.Random) -> str:
    return line.format(
        money=rng.choice(["1,200円", "￥3,500", "12万円", "4,800円"]),
        serial=rng.choice(["SN: RYU-0001-AX", "製造番号 FLT-7781-ZZ", "S/N KMO-3141-59"]),
        url=f"https://example.invalid/docs/{rng.randint(100, 999)}",
        phone=f"000-{rng.randint(1000, 9999)}-{rng.randint(1000, 9999)}",
        email=f"{rng.choice(PEOPLE)[1]}@example.invalid",
    )


def body(topic: dict[str, object], rng: random.Random, to_name: str, me: str, quote: str) -> str:
    lines = list(topic["lines"])  # type: ignore[call-overload]
    picked = rng.sample(lines, k=min(len(lines), rng.randint(2, 3)))
    parts = [f"{to_name.split()[0]}さん", "", rng.choice(OPENINGS), f"{me.split()[0]}です。", ""]
    parts += [fill(s, rng) for s in picked]
    # 半分は本文の途中に引用を挟む（署名より上にある引用行を落とすルールの確認用）
    if quote and rng.random() < 0.5:
        parts += ["", "> " + quote.splitlines()[0]]
        quote = ""
    parts += ["", rng.choice(CLOSINGS), "", "--", me, f"浮遊島 第{rng.randint(1, 3)}竜舎 事務棟"]
    parts += [f"TEL 000-{rng.randint(1000, 9999)}-{rng.randint(1000, 9999)}", "", DISCLAIMER]
    if quote:
        parts += ["", "> " + quote.replace("\n", "\n> ")]
    return "\n".join(parts) + "\n"


def main() -> None:
    rng = random.Random(20310401)
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.eml"):
        old.unlink()  # 生成物の作り直し（DB のデータではない）
    start = datetime(2031, 4, 1, 9, 0, tzinfo=JST)
    n = 0
    thread_no = 0
    while n < 50:
        topic = TOPICS[thread_no % len(TOPICS)]
        thread_no += 1
        root_id = f"<fx-{thread_no:03d}-0@example.invalid>"
        refs: list[str] = []
        at = start + timedelta(days=thread_no * 2, hours=rng.randint(0, 8))
        prev_text = ""
        for _ in range(rng.randint(2, 5)):
            if n >= 50:
                break
            sender, recipient = rng.sample(PEOPLE, 2)
            msg = EmailMessage()
            msg_id = root_id if not refs else f"<fx-{thread_no:03d}-{len(refs)}@example.invalid>"
            msg["Message-ID"] = msg_id
            msg["Subject"] = ("Re: " if refs else "") + f"【架空】{topic['subject']}"
            msg["From"] = f"{sender[1]}@example.invalid"
            msg["To"] = f"{recipient[1]}@example.invalid"
            msg["Date"] = format_datetime(at)
            msg["X-Fixture"] = "fictional"
            if refs:
                msg["In-Reply-To"] = refs[-1]
                msg["References"] = " ".join(refs)
            text = body(topic, rng, recipient[0], sender[0], prev_text)
            msg.set_content(text)
            n += 1
            (OUT / f"{n:04d}.eml").write_bytes(bytes(msg))
            refs.append(msg_id)
            prev_text = text.split("\n\n", 2)[-1][:200]
            at += timedelta(hours=rng.randint(1, 30))
    print(f"{n} 通を作成: {OUT}")


if __name__ == "__main__":
    main()
