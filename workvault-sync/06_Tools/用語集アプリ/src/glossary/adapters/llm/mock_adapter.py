"""Phase 0 の既定の LLM。外に出ず、同じ入力には必ず同じ出力を返す。

乱数は Python 組込みの hash() ではなく sha256 から作る。hash() は起動ごとに値が変わるので、
テストの期待値もデモの表示も毎回ずれてしまう。
"""

from __future__ import annotations

import hashlib
import math
import random
from typing import Any

MOCK_MODEL_NAME = "mock-llm"


def _rng(text: str, seed: int) -> random.Random:
    digest = hashlib.sha256(f"{seed}:{text}".encode()).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def _target_word(prompt: str) -> str:
    # プロンプト側の約束として「対象語: X」の行を入れている。無ければ語を出さない
    for line in prompt.splitlines():
        if line.startswith("対象語:"):
            return line.split(":", 1)[1].strip()
    return ""


class MockLlmAdapter:
    def __init__(self, seed: int = 0, dim: int = 16) -> None:
        self.seed = seed
        self.dim = dim
        self.model_name = MOCK_MODEL_NAME

    def _fill(self, key: str, spec: dict[str, Any], rng: random.Random, word: str) -> Any:
        if "enum" in spec:
            return rng.choice(list(spec["enum"]))
        kind = spec.get("type")
        if kind == "string":
            if key == "definition":
                subject = f"『{word}』は" if word else "この語は"
                return f"【モック草案】{subject}架空データの中で繰り返し現れる語。実データで要確認。"
            return f"【モック】{key}"
        if kind == "number":
            return round(rng.uniform(float(spec.get("minimum", 0)), float(spec.get("maximum", 1))), 3)
        if kind == "integer":
            return rng.randint(int(spec.get("minimum", 0)), int(spec.get("maximum", 10)))
        if kind == "boolean":
            return rng.random() < 0.5
        if kind == "array":
            return []
        if kind == "object":
            return self._object(spec, rng, word)
        return None

    def _object(self, schema: dict[str, Any], rng: random.Random, word: str) -> dict[str, Any]:
        props: dict[str, Any] = schema.get("properties", {})
        return {k: self._fill(k, v, rng, word) for k, v in props.items()}

    def complete_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        return self._object(schema, _rng(prompt, self.seed), _target_word(prompt))

    def embed(self, texts: list[str]) -> list[list[float]]:
        out = []
        for t in texts:
            rng = _rng(t, self.seed)
            v = [rng.gauss(0, 1) for _ in range(self.dim)]
            norm = math.sqrt(sum(x * x for x in v)) or 1.0
            out.append([x / norm for x in v])
        return out
