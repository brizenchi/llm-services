from fastapi import APIRouter
import logging
import time
from pkg.core.result.result import success_result
logger = logging.getLogger(__name__)

router = APIRouter(tags=["users"])

@router.get("/")
async def read_users():
    logger.info("read_users")
    time.sleep(1)
    return success_result(data=[{"username": "Rick"}, {"username": "Morty"}])

@router.get("/me")
async def read_user_me():
    return success_result(data={"username": "fakecurrentuser"})

@router.get("/{username}")
async def read_user(username: str):
    return success_result(data={"username": username})
