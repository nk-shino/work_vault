"""社内 LiteLLM ゲートウェイ用アダプタ。既定では使わない（LLM_BACKEND=litellm のときだけ）。

2026-09-29 に管理画面で確かめたこと：OpenAI 互換の API（/v1/chat/completions）で、
アプリ用の鍵が発行済み。モデルは Azure の gpt-5 系が並んでいる。
埋め込み用のモデルは画面の範囲では見えていないので、embed は呼べるようにだけしてある。

openai SDK ではなく標準ライブラリの urllib で呼ぶ。理由は2つ。
- 依存を増やさない（社用PCへ運ぶ wheel が増えない）
- urllib は Windows の証明書ストアを使うので、会社の SSL 検査があっても通りやすい
  （SDK が使う httpx は certifi の証明書しか見ない）

接続先・鍵・モデル名は環境変数から読む。値はリポジトリに書かない。
"""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Any
from urllib.parse import urlparse

ENV_VARS = ("LITELLM_BASE_URL", "LITELLM_API_KEY", "LITELLM_CHAT_MODEL", "LITELLM_EMBED_MODEL")
TIMEOUT_SEC = 60


class LlmError(RuntimeError):
    pass


def parse_chat_json(response: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    """chat/completions の応答から JSON を取り出し、必須の項目が揃っているかを確かめる。

    通信とは切り離してある。応答の形が想定と違ったときの振る舞いを、通信なしでテストするため。
    """
    try:
        content = response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        raise LlmError(f"応答の形が想定と違う: {e}") from e
    text = str(content).strip()
    # コードブロックで囲んで返すモデルがあるので外す
    if text.startswith("```"):
        text = text.strip("`").removeprefix("json").strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise LlmError("JSON として読めない応答") from e
    if not isinstance(data, dict):
        raise LlmError("JSON のオブジェクトではない応答")
    missing = [k for k in schema.get("required", []) if k not in data]
    if missing:
        raise LlmError(f"必須の項目が無い: {missing}")
    return data


def parse_embeddings(response: dict[str, Any], count: int) -> list[list[float]]:
    try:
        rows = sorted(response["data"], key=lambda r: r["index"])
        vectors = [[float(x) for x in r["embedding"]] for r in rows]
    except (KeyError, TypeError, ValueError) as e:
        raise LlmError(f"埋め込みの応答の形が想定と違う: {e}") from e
    if len(vectors) != count:
        raise LlmError(f"埋め込みの件数が合わない（{count} 件送って {len(vectors)} 件）")
    return vectors


class LiteLlmAdapter:
    def __init__(self) -> None:
        self.base_url = os.environ.get("LITELLM_BASE_URL", "").strip().rstrip("/")
        self.api_key = os.environ.get("LITELLM_API_KEY", "").strip()
        self.chat_model = os.environ.get("LITELLM_CHAT_MODEL", "").strip()
        self.embed_model = os.environ.get("LITELLM_EMBED_MODEL", "").strip()
        missing = [n for n, v in zip(ENV_VARS[:3], (self.base_url, self.api_key, self.chat_model), strict=True) if not v]
        if missing:
            raise RuntimeError(f"LLM_BACKEND=litellm には環境変数が必要: {missing}")
        # 鍵を平文の通信に載せない
        if urlparse(self.base_url).scheme != "https":
            raise RuntimeError("LITELLM_BASE_URL は https:// で始めること")
        self.model_name = self.chat_model

    def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        req = urllib.request.Request(
            self.base_url + path,
            data=json.dumps(body).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as res:
                return dict(json.loads(res.read().decode("utf-8")))
        except OSError as e:
            # 鍵が例外の文面に混ざらないよう、接続先のパスと種類だけを返す
            raise LlmError(f"LiteLLM への接続に失敗: {path}: {type(e).__name__}") from None

    def complete_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        body = {
            "model": self.chat_model,
            "messages": [
                {
                    "role": "system",
                    "content": "JSON オブジェクトだけを返してください。次の JSON Schema に従うこと: "
                    + json.dumps(schema, ensure_ascii=False),
                },
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
        }
        try:
            return parse_chat_json(self._post("/chat/completions", body), schema)
        except LlmError:
            # JSON モードに対応していないモデルもあるので、指定を外して1回だけやり直す
            body.pop("response_format")
            return parse_chat_json(self._post("/chat/completions", body), schema)

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not self.embed_model:
            raise RuntimeError("埋め込みには LITELLM_EMBED_MODEL が必要（使えるモデルは未確認）")
        res = self._post("/embeddings", {"model": self.embed_model, "input": texts})
        return parse_embeddings(res, len(texts))
