from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def documents_root():
    return {"message": "Documents endpoint placeholder"}
