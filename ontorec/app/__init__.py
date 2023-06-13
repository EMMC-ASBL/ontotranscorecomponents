"""
app init
"""
import logging
from importlib import import_module
from fastapi import FastAPI, Depends
from app.ontotrans_api import core
from app.ontotrans_api.routers import databases, namespaces
from pydantic import Field
from app.config.ontoRECSettings import OntoRECSetting
from typing import TYPE_CHECKING


if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, Dict, List


__version__: str = "1.0.0"
__prefix__: str = "/ontorec/api/v{}".format(__version__.split('.', maxsplit=1)[0])
app_settings = OntoRECSetting()


logger = logging.getLogger(__name__)
logger.setLevel(app_settings.LOG_LEVEL)



def get_auth_deps() -> "List[Depends]": #type: ignore

    if app_settings.AUTHENTICATION_DEPENDENCIES:
        modules = [
            module.strip().split(":")
            for module in app_settings.AUTHENTICATION_DEPENDENCIES.split("|")
        ]
        imports = [
            getattr(import_module(module), classname) for (module, classname) in modules
        ]
        logger.info("Imported the following dependencies for authentication: %s", imports)
        dependencies = [Depends(dependency) for dependency in imports]
    else:
        dependencies = []
        logger.info("No dependencies for authentication assigned.")

    return dependencies


def create_app():
    """
    Create the FastAPI app
    """
    logger.info("TEST INFO")
    app = FastAPI(dependencies=get_auth_deps())
    app.include_router(core.router, prefix = __prefix__)
    app.include_router(databases.router, prefix = __prefix__)
    app.include_router(namespaces.router, prefix = __prefix__)


    return app
