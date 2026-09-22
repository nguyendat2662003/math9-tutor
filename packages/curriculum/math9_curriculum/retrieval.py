"""[Đã chuyển] Tầng truy xuất giờ nằm ở packages/retrieval.

RAG phục vụ Solver, không thuộc về curriculum. File này giữ lại để tương thích
ngược; import từ math9_retrieval thay thế.
"""

from __future__ import annotations

import warnings

warnings.warn(
    "math9_curriculum.retrieval đã chuyển sang math9_retrieval.service",
    DeprecationWarning, stacklevel=2,
)

try:
    from math9_retrieval.service import RagService, RetrievedContext  # noqa: F401
    from math9_retrieval.store import Doc, load_methods  # noqa: F401
except ImportError:
    pass
