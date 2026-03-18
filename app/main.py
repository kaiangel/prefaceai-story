"""FastAPI application entry point"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.database import init_db, close_db
from app.api import api_router
from app.api.images import router as images_router
from app.api.audio import router as audio_router
from app.config import settings
from app.middleware.log_sanitizer import install as install_log_sanitizer

# 日志脱敏：在任何输出之前安装
install_log_sanitizer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    await init_db()

    # 确保图像和音频存储目录存在
    os.makedirs(settings.IMAGE_STORAGE_PATH, exist_ok=True)
    os.makedirs(settings.AUDIO_STORAGE_PATH, exist_ok=True)

    yield
    # Shutdown
    await close_db()


app = FastAPI(
    title="序话Story API",
    description="AI短视频/短剧生成应用 - Phase 3: 音频合成与音画对齐",
    version="0.3.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://prefaceai.mov",
        "http://localhost:3000",  # 本地前端开发
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)
app.include_router(images_router)
app.include_router(audio_router)


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
