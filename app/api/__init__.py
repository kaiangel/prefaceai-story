"""API routers"""

from fastapi import APIRouter
from app.api import auth, projects, chapters

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(projects.router)
api_router.include_router(chapters.router)
