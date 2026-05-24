"""全局异常处理器 — 统一错误响应格式，避免泄漏内部细节。"""
import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.config import settings

logger = logging.getLogger("rsod")

CORS_ORIGINS = settings.CORS_ORIGINS


def _add_cors(response: JSONResponse, request: Request) -> JSONResponse:
    origin = request.headers.get("origin")
    if origin in CORS_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
    return response


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.warning("HTTP %d: %s", exc.status_code, exc.detail)
    return _add_cors(JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": str(exc.detail), "code": exc.status_code},
    ), request)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning("Validation: %s", exc.errors())
    return _add_cors(JSONResponse(
        status_code=422,
        content={"success": False, "message": "请求参数格式错误", "code": 422},
    ), request)


async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled: %s: %s", type(exc).__name__, exc, exc_info=True)
    return _add_cors(JSONResponse(
        status_code=500,
        content={"success": False, "message": "服务器内部错误，请联系管理员", "code": 500},
    ), request)
