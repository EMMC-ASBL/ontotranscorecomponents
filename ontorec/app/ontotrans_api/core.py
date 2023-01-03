"""
    Home router
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def home():
    """
    Home endpoint
    """
    return {"msg": "OntoREC v0.1"}

