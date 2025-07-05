
from fastapi import APIRouter

router = APIRouter()

@router.get("/users/me")
async def read_users_me():
    return {"message": "User profile endpoint"}


