from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.db_models import User
from app.models.schemas import LoginRequest, RegisterRequest
from app.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.services.redis_service import redis_service
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

AUTH_RATE_LIMIT = 10  # 每窗口最多 10 次
AUTH_RATE_WINDOW = 60  # 窗口 60 秒


async def _check_auth_rate(key: str):
    """认证接口通用限流检查。"""
    allowed = await redis_service.check_rate_limit_str(key, AUTH_RATE_LIMIT, AUTH_RATE_WINDOW)
    if not allowed:
        raise HTTPException(status_code=429, detail="请求过于频繁，请 60 秒后再试")


@router.post("/login")
async def login(req: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """邮箱或用户名 + 密码登录, 返回 JWT token pair"""
    client_ip = request.client.host if request.client else "unknown"
    await _check_auth_rate(f"auth:login:{client_ip}:{req.account}")

    user = db.query(User).filter(
        (User.username == req.account) | (User.email == req.account)
    ).first()

    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="账号或密码错误",
        )

    token_data = {"sub": user.username, "user_id": user.id}
    return {
        "success": True,
        "message": "登录成功",
        "data": {
            "access_token": create_access_token(token_data),
            "refresh_token": create_refresh_token(token_data),
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "avatar": user.avatar,
            },
        },
    }


@router.post("/register")
async def register(req: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    """注册新用户"""
    client_ip = request.client.host if request.client else "unknown"
    await _check_auth_rate(f"auth:register:{client_ip}")

    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="用户名已存在")
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="邮箱已注册")

    # 密码复杂度
    if len(req.password) < 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="密码至少 6 位")

    user = User(
        username=req.username,
        email=req.email,
        hashed_password=hash_password(req.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"success": True, "message": "注册成功"}


@router.post("/refresh")
async def refresh_token(refresh_token: str, request: Request, db: Session = Depends(get_db)):
    """用 refresh token 换取新的 access token"""
    client_ip = request.client.host if request.client else "unknown"
    await _check_auth_rate(f"auth:refresh:{client_ip}")

    try:
        payload = decode_token(refresh_token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的 refresh token")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="请使用 refresh token")

    username = payload.get("sub")
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")

    token_data = {"sub": user.username, "user_id": user.id}
    return {
        "success": True,
        "data": {
            "access_token": create_access_token(token_data),
            "token_type": "bearer",
        },
    }


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return {
        "success": True,
        "data": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "role": current_user.role,
            "avatar": current_user.avatar,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        },
    }
