"""ドメイン層の例外。画面は種類ごとに応答を変える。"""

from __future__ import annotations

from typing import Any


class ValidationFailed(Exception):
    """入力や状態が約束事を満たさない。"""


class ConflictError(Exception):
    """楽観ロックの競合。画面を開いた時点の版が既に古い。"""

    def __init__(
        self, snapshot: dict[str, Any], changes: dict[str, Any], expected_revision: int
    ) -> None:
        super().__init__("他の操作が先に保存したため競合した（楽観ロック）")
        self.snapshot = snapshot
        self.changes = changes
        self.expected_revision = expected_revision


class NotFound(Exception):
    """対象が見つからない。"""
