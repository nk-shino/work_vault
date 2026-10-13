"""環境変数に従ってアダプタを選ぶ。コアはこの関数経由でしかアダプタに触れない。"""

from __future__ import annotations

import os

from glossary.adapters.llm.mock_adapter import MockLlmAdapter
from glossary.adapters.source.export_file_adapter import ExportFileAdapter
from glossary.ports import LlmPort, SourcePort
from glossary.settings import Settings

# テスト中は conftest がこれを立てる。モック以外が選ばれたら、その場で止める
TESTING_FLAG = "GLOSSARY_TESTING"


def make_source(settings: Settings) -> SourcePort:
    if settings.source_backend == "export":
        return ExportFileAdapter(settings.export_dir)
    from glossary.adapters.source.knowledge_api_adapter import KnowledgeApiAdapter

    return KnowledgeApiAdapter()


def make_llm(settings: Settings) -> LlmPort:
    if settings.llm_backend != "mock" and os.environ.get(TESTING_FLAG) == "1":
        raise RuntimeError(f"テスト中は LLM_BACKEND=mock 以外を使わない: {settings.llm_backend}")
    if settings.llm_backend == "mock":
        return MockLlmAdapter()
    # 実装側の import はここで初めて行う。オプショナル依存が無くても mock は動かすため
    if settings.llm_backend == "litellm":
        from glossary.adapters.llm.litellm_adapter import LiteLlmAdapter

        return LiteLlmAdapter()
    from glossary.adapters.llm.local_embedding_adapter import LocalEmbeddingAdapter

    return LocalEmbeddingAdapter()


def model_name(llm: LlmPort) -> str:
    return str(getattr(llm, "model_name", type(llm).__name__))
