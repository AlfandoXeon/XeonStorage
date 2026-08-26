from fastapi import APIRouter
router=APIRouter(tags=["System"])
@router.get("/api/health")
def health(): return {"success":True,"status":"ok"}
