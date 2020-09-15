from fastapi import APIRouter

from . import builds, service

router = APIRouter()


router.include_router(service.router)
router.include_router(builds.router, tags=["build"], prefix="/build")
