"""sentence-transformers による埋め込みの代替実装（骨格のみ）。

社内の埋め込み API が使えなかったときの逃げ道。依存はオプショナルで、
未インストールでも他の機能は動く（import はこのクラスを作ったときにだけ行う）。

sentence-transformers は既定だと初回にモデルをインターネットから取りに行く。
社用PCでそれが通るとは限らず、Phase 0 のオフライン方針とも合わないので、
手元に置いたモデルのフォルダを指定したときだけ動き、ダウンロードは禁止する。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


class LocalEmbeddingAdapter:
    def __init__(self, model_dir: str | None = None) -> None:
        path = model_dir or os.environ.get("LOCAL_EMBED_MODEL_DIR", "")
        if not path or not Path(path).is_dir():
            raise RuntimeError("LOCAL_EMBED_MODEL_DIR に手元のモデルフォルダを指定すること")
        # ダウンロードを試みないよう、import より前にオフライン指定を入れる
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            raise RuntimeError("pip install -e .[local] が必要") from e
        self._model = SentenceTransformer(path)
        self.model_name = f"local:{Path(path).name}"

    def complete_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("ローカル実装は埋め込み専用。生成は扱わない")

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = self._model.encode(texts, normalize_embeddings=True)
        return [list(map(float, v)) for v in vectors]
