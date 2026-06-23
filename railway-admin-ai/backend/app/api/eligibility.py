from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def eligibility_root():
    return {"message": "Eligibility endpoint placeholder"}
