"""
app init
"""
from fastapi import FastAPI
from app.ontotrans_api import core
from app.ontotrans_api.routers import databases


def create_app():
    """
    Create the FastAPI app
    """
    app = FastAPI()
    app.include_router(core.router)
    app.include_router(databases.router)
    return app
