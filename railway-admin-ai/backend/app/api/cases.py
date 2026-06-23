from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def cases_root():
    return {"message": "Cases endpoint placeholder"}
