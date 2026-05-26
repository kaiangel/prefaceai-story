"""FastAPI application entry point"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from app.database import init_db, close_db
from app.api import api_router
from app.api.images import router as images_router
from app.api.audio import router as audio_router
from app.api.utils import router as utils_router
import app.models  # noqa: F401
from app.config import settings
from app.middleware.log_sanitizer import install as install_log_sanitizer
from app.middleware.db_retry import DBConnectionRetryMiddleware

# 日志脱敏：在任何输出之前安装
install_log_sanitizer()

# 永久日志：Python logging 同时写终端 + 文件
import logging

os.makedirs("storage/logs", exist_ok=True)
_file_handler = logging.FileHandler("storage/logs/backend.log", encoding="utf-8")
_file_handler.setLevel(logging.INFO)
_file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        _file_handler,
    ],
)
# 让 uvicorn 的 HTTP 日志也写到文件
logging.getLogger("uvicorn.access").addHandler(_file_handler)
logging.getLogger("uvicorn.error").addHandler(_file_handler)

logger = logging.getLogger("xuhua")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("[Main] Application startup: initializing database...")
    await init_db()
    logger.info("[Main] Database initialized successfully")

    # 确保图像和音频存储目录存在
    os.makedirs(settings.IMAGE_STORAGE_PATH, exist_ok=True)
    os.makedirs(settings.AUDIO_STORAGE_PATH, exist_ok=True)
    logger.info(f"[Main] Storage dirs ready: {settings.IMAGE_STORAGE_PATH}, {settings.AUDIO_STORAGE_PATH}")

    yield
    # Shutdown
    logger.info("[Main] Application shutdown: closing database...")
    await close_db()
    logger.info("[Main] Database closed")


app = FastAPI(
    title="序话Story API",
    description="AI短视频/短剧生成应用 - Phase 3: 音频合成与音画对齐",
    version="0.3.0",
    lifespan=lifespan,
)

# Wave 13 #5d: connection-level retry middleware (transient MySQL 2013/2003 → 幂等 GET 自动重试 1 次)
# 注意 add_middleware 顺序: 后添加的更外层。先加 retry → 后加 CORS → CORS 在最外层,
# 保证即使 retry 最终重抛错误, 响应仍带 CORS 头 (前端能正常读到错误)。
# retry 只包裹路由层, 只重试 GET/HEAD, 不重试写操作, 限 1 次, 不掩盖非 transient 错误。
app.add_middleware(DBConnectionRetryMiddleware)

# CORS middleware (最外层)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://prefaceai.mov",
        "http://localhost:3000",  # 本地前端开发
        "http://127.0.0.1:3000",  # 本地前端开发
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static mount: pipeline 产物（图像 / BGM / 参考图）统一通过 /static/outputs/{uuid}/... 访问
# 对应文件系统路径: ./output/{project_uuid}/...
_outputs_dir = os.path.abspath("output")
os.makedirs(_outputs_dir, exist_ok=True)
app.mount("/static/outputs", StaticFiles(directory=_outputs_dir), name="static_outputs")

# Include API routes
app.include_router(api_router)
app.include_router(images_router)
app.include_router(audio_router)
app.include_router(utils_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    B37: 全局 500 异常捕获 — 记录 stack trace + 返回结构化错误
    所有未被路由层 try/except 捕获的异常都会到这里
    """
    logger.exception(
        f"[Global] Unhandled exception: {request.method} {request.url} — {exc}"
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "path": str(request.url.path),
            "method": request.method,
        },
    )


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "name": "序话Story API",
        "version": "0.3.0",
        "status": "running",
        "phase": "Phase 3 - Audio Synthesis & Alignment",
    }


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
