from __future__ import annotations

from typing import Any


class DomainError(Exception):
    """利用者に理由をそのまま見せてよい失敗。"""


class ValidationFailed(DomainError):
    pass


class NotFound(DomainError):
    pass


class ConflictError(DomainError):
    """他の人が先に更新していた。上書きせず、双方の内容を呼び出し元へ返す。"""

    def __init__(
        self, current: dict[str, Any], submitted: dict[str, Any], expected_revision: int
    ) -> None:
        super().__init__(
            f"版が一致しない（編集開始時 {expected_revision} / 現在 {current.get('revision_number')}）"
        )
        self.current = current
        self.submitted = submitted
        self.expected_revision = expected_revision
