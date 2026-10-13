"""テストではモック以外の LLM を使わない。外への通信も起きない。"""

from __future__ import annotations

import os
import socket
from dataclasses import replace

import pytest
from conftest import NetworkBlocked

from glossary.adapters.llm.mock_adapter import MockLlmAdapter
from glossary.factory import make_llm
from glossary.settings import load_settings


def test_tests_run_with_mock_backend() -> None:
    assert os.environ["LLM_BACKEND"] == "mock"
    assert isinstance(make_llm(load_settings()), MockLlmAdapter)


@pytest.mark.parametrize("backend", ["litellm", "local"])
def test_non_mock_backend_refused_during_tests(backend: str) -> None:
    # アダプタを作る前に止まる（litellm の骨格も local の import も走らない）
    with pytest.raises(RuntimeError, match="mock 以外"):
        make_llm(replace(load_settings(), llm_backend=backend))


def test_mock_is_deterministic() -> None:
    schema = {"type": "object", "properties": {"definition": {"type": "string"},
              "confidence": {"type": "number", "minimum": 0, "maximum": 1}}}  # fmt: skip
    a = MockLlmAdapter().complete_json("対象語: 竜舎", schema)
    b = MockLlmAdapter().complete_json("対象語: 竜舎", schema)
    assert a == b
    assert "竜舎" in a["definition"]
    v = MockLlmAdapter().embed(["竜舎", "竜車"])
    assert len(v) == 2 and v[0] != v[1] and v == MockLlmAdapter().embed(["竜舎", "竜車"])


def test_external_connection_is_blocked() -> None:
    # 203.0.113.0/24 は文書用に予約されたアドレスで、どこにも届かない
    with pytest.raises(NetworkBlocked), socket.socket() as s:
        s.connect(("203.0.113.1", 80))
