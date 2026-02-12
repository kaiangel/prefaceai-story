"""Authentication API - MVP version with hardcoded test accounts"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/auth", tags=["auth"])

# MVP test accounts
DEMO_USERS = {
    "demo001": {"name": "测试用户A", "password": "demo123"},
    "demo002": {"name": "测试用户B", "password": "demo456"},
    "kai": {"name": "Kai", "password": "xuhua2024"},
}


class LoginRequest(BaseModel):
    user_id: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    user_id: str
    name: str
    token: str  # MVP: just the user_id itself


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    MVP login endpoint

    Test accounts:
    - demo001 / demo123
    - demo002 / demo456
    - kai / xuhua2024
    """
    user = DEMO_USERS.get(request.user_id)
    if not user or user["password"] != request.password:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    return LoginResponse(
        success=True,
        user_id=request.user_id,
        name=user["name"],
        token=request.user_id,  # MVP simplified
    )


@router.get("/me")
async def get_current_user(token: str):
    """Get current user info by token"""
    user = DEMO_USERS.get(token)
    if not user:
        raise HTTPException(status_code=401, detail="无效的token")

    return {
        "user_id": token,
        "name": user["name"],
    }
