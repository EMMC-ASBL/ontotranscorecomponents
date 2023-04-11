"""
app init
"""
from fastapi import FastAPI
from app.ontotrans_api import core
from app.ontotrans_api.routers import databases, namespaces
from app.ontotrans_api.handlers.triplestore_configuration import load_docker_configuration


def create_app():
    """
    Create the FastAPI app
    """
    app = FastAPI()
    app.include_router(core.router)
    app.include_router(databases.router)
    app.include_router(namespaces.router)

    app.add_event_handler("startup", load_docker_configuration)

    return app
