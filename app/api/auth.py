"""Authentication and account APIs."""

from __future__ import annotations

from datetime import datetime
import hashlib
import hmac
import os
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.invite_code import InviteCode
from app.models.invite_relationship import InviteRelationship
from app.models.user import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


def user_now() -> datetime:
    return datetime.utcnow()


def _hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        120000,
    ).hex()
    return f"{salt}${digest}"


def _verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt, digest = stored_hash.split("$", 1)
    except ValueError:
        return False
    expected = _hash_password(password, salt)
    return hmac.compare_digest(expected, f"{salt}${digest}")


def _extract_token(
    authorization: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None, alias="X-User-ID"),
) -> str:
    if authorization and authorization.startswith("Bearer "):
        return authorization.removeprefix("Bearer ").strip()
    if x_user_id:
        return x_user_id
    raise HTTPException(status_code=401, detail="未登录")


async def get_current_user(
    token: str = Depends(_extract_token),
    db: AsyncSession = Depends(get_db),
) -> User:
    result = await db.execute(select(User).where(User.uuid == token))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="无效的登录状态")
    return user


class UserProfile(BaseModel):
    id: str
    email: EmailStr
    name: str
    avatar_url: str | None = None
    plan: str
    credits: int
    created_at: str


class AuthResponse(BaseModel):
    success: bool
    token: str
    user: UserProfile


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    invite_code: str = Field(..., min_length=1, max_length=64)


class UpdateProfileRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    avatar_url: str | None = Field(default=None, max_length=500)


class PricingPlan(BaseModel):
    key: str
    name: str
    subtitle: str
    price: str
    period: str
    credits: int | None = None
    features: list[str]


class PricingResponse(BaseModel):
    plans: list[PricingPlan]


def _serialize_user(user: User) -> UserProfile:
    return UserProfile(
        id=user.uuid or str(user.id),
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url,
        plan=user.plan,
        credits=user.credits,
        created_at=user.created_at.isoformat(),
    )


@router.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    invite_code_value = request.invite_code.strip().upper()

    invite_code_result = await db.execute(
        select(InviteCode).where(InviteCode.code == invite_code_value)
    )
    invite_code = invite_code_result.scalar_one_or_none()
    if not invite_code:
        raise HTTPException(status_code=400, detail="邀请码无效")
    if invite_code.status != "active":
        raise HTTPException(status_code=400, detail="邀请码不可用")
    if invite_code.expires_at and invite_code.expires_at <= user_now():
        raise HTTPException(status_code=400, detail="邀请码已过期")
    if invite_code.used_count >= invite_code.max_uses:
        raise HTTPException(status_code=400, detail="邀请码已用完")

    existing = await db.execute(select(User).where(User.email == request.email.lower()))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="邮箱已注册")

    user = User(
        uuid=str(uuid4()),
        email=request.email.lower(),
        name=request.email.split("@")[0],
        password_hash=_hash_password(request.password),
        invited_by_user_id=invite_code.owner_user_id,
        used_invite_code_id=invite_code.id,
    )
    db.add(user)
    await db.flush()

    invite_code.used_count += 1
    if invite_code.used_count >= invite_code.max_uses:
        invite_code.status = "exhausted"
    db.add(invite_code)

    db.add(
        InviteRelationship(
            invite_code_id=invite_code.id,
            inviter_user_id=invite_code.owner_user_id,
            invitee_user_id=user.id,
        )
    )

    return AuthResponse(success=True, token=user.uuid or str(user.id), user=_serialize_user(user))


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == request.email.lower()))
    user = result.scalar_one_or_none()
    if not user or not _verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="邮箱或密码错误")

    return AuthResponse(success=True, token=user.uuid or str(user.id), user=_serialize_user(user))


@router.get("/me", response_model=UserProfile)
async def me(user: User = Depends(get_current_user)):
    return _serialize_user(user)


@router.put("/me", response_model=UserProfile)
async def update_me(
    request: UpdateProfileRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user.name = request.name.strip()
    user.avatar_url = request.avatar_url
    db.add(user)
    await db.flush()
    return _serialize_user(user)


@router.get("/pricing", response_model=PricingResponse)
async def pricing():
    return PricingResponse(
        plans=[
            PricingPlan(
                key="free",
                name="Free",
                subtitle="免费体验",
                price="¥0",
                period="",
                credits=10,
                features=["1-2 个故事/月", "基础 3 种风格", "标准排队"],
            ),
            PricingPlan(
                key="pro",
                name="Pro",
                subtitle="邀请码用户专享",
                price="¥XX",
                period="/月",
                credits=100,
                features=["~30 个故事/月", "15 种风格", "优先排队", "视频合成"],
            ),
            PricingPlan(
                key="max",
                name="Max",
                subtitle="专业无限",
                price="¥XX",
                period="/月",
                credits=None,
                features=["不限故事数", "API 接口", "专属客服"],
            ),
        ]
    )
