"""
app init
"""
from fastapi import FastAPI
from app.ontotrans_api import core
from app.ontotrans_api.routers import databases, namespaces

from app.config.triplestoreConfig import TriplestoreConfig
from app.config.ontokbCredentials import OntoKBCredentials


def create_app():
    """
    Create the FastAPI app
    """
    app = FastAPI()
    app.include_router(core.router)
    app.include_router(databases.router)
    app.include_router(namespaces.router)


    triplestore_config = TriplestoreConfig()
    ontokbcredentials_config = OntoKBCredentials()
    print("Loading configuration...")
    print("-----------------------------------------")
    print("+ ONTOKB HOST: {}".format(triplestore_config.ONTOKB_HOST))
    print("+ ONTOKB PORT: {}".format(triplestore_config.ONTOKB_PORT))
    print("+ ONTOKB BACKEND: {}".format(triplestore_config.ONTOKB_BACKEND))
    print("+ ONTOKB UNAME: {}".format(ontokbcredentials_config.ONTOKB_USERNAME))
    print("+ ONTOKB PWD: {}".format(ontokbcredentials_config.ONTOKB_PASSWORD))
    print("-----------------------------------------")


    return app
