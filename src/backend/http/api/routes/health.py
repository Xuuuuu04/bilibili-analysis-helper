from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health_check():
    return {"success": True, "status": "running", "message": "BiliBili智能学习平台 Ultra版运行中"}
