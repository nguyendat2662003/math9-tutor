from fastapi import APIRouter
from math9_curriculum.loader import curriculum

router = APIRouter()


@router.get("/health")
def health() -> dict:
    cm = curriculum()
    return {"status": "ok", "topics": len(cm.topics), "goal_types": len(cm.all_goal_types())}
