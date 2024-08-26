from fastapi import APIRouter

from .auth import router as auth_router
from .organizations import router as organizations_router
from .platform import router as platform_router

# from .conversations import router as conversations_router
from .users import router as users_router

router = APIRouter()

router.include_router(auth_router, tags=["auth"])
router.include_router(platform_router, tags=["platform"])
router.include_router(organizations_router, tags=["organizations"])
router.include_router(users_router, tags=["organizations.users"])
# router.include_router(
#     conversations_router, prefix="/conversations", tags=["conversations"]
# )
