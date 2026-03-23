"""API routers"""

from fastapi import APIRouter
from app.api import auth, beta_applications, chapters, contact_us, projects

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(beta_applications.router)
api_router.include_router(projects.router)
api_router.include_router(chapters.router)
api_router.include_router(contact_us.router)
