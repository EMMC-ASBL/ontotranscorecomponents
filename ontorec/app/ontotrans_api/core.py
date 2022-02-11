"""
    Home router
"""
from fastapi import APIRouter

router = APIRouter()

connection_details = {
    'endpoint': 'http://stardog:5820',
    'username': 'admin',
    'password': 'admin'
}

@router.get("/")
async def home():
    """
    Home endpoint
    """
    return {"msg": "OntoREC v0.1"}
