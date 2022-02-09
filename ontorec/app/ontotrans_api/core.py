"""
    Home router
"""

from fastapi import APIRouter, File, UploadFile

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
    return {"msg": "OntoTrans FastAPI v0.1"}
