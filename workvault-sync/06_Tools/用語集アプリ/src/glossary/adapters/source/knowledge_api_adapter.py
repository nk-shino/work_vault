"""既存のメールナレッジ化AI から取得するためのアダプタ（スタブ）。

仕様が判明するまで実装しない。
社内にこのシステムがあるらしいことまでは分かっているが、スニペットを取り出せるのか、
どんな形式・認証・件数制限なのかは確認できていない。推測で書くと、仕様が判明したときに
推測部分がそのまま残って手戻りになるので、インタフェースに合わせた形だけを置く。
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from glossary.ports import RawDocument


class KnowledgeApiAdapter:
    def fetch_documents(self, since: datetime, until: datetime) -> Iterable[RawDocument]:
        raise NotImplementedError(
            "メールナレッジ化AI の仕様が未確定のため未実装。SOURCE_BACKEND=export を使うこと"
        )
