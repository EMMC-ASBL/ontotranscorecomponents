"""
app init
"""
from fastapi import FastAPI
from app.ontotrans_api.core import router
from app.ontotrans_api import core


def create_app():
    """
    Create the FastAPI app
    """
    app = FastAPI()
    app.include_router(router)
    return app
