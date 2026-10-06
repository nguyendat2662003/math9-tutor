from fastapi import APIRouter
from math9_core.enums import GOAL_TYPE_VI
from math9_curriculum.loader import curriculum

router = APIRouter(prefix="/api")


@router.get("/health")
def health() -> dict:
    cm = curriculum()
    return {"status": "ok", "topics": len(cm.topics), "goal_types": len(cm.all_goal_types())}


@router.get("/topics")
def topics() -> dict:
    """Danh mục chuyên đề và dạng mục tiêu — frontend dùng để hiển thị nhãn tiếng Việt."""
    cm = curriculum()
    return {
        "topics": {t.id: t.name for t in cm.topics.values()},
        "goal_types": GOAL_TYPE_VI,
    }
