import os

TRIPLESTORE_HOST = None
TRIPLESTORE_PORT = None
TRIPLESTORE_TYPE = None

__supported_backend = ["stardog"]


def load_docker_configuration():
    global TRIPLESTORE_HOST,TRIPLESTORE_PORT,TRIPLESTORE_TYPE

    TRIPLESTORE_HOST = os.getenv("ONTOKB_HOST")
    TRIPLESTORE_PORT = os.getenv("ONTOKB_PORT")
    TRIPLESTORE_TYPE = os.getenv("ONTOKB_BACKEND")

    ## Check if all parameters are defined
    if TRIPLESTORE_TYPE == None:
        raise Exception("Parameter TRIPLESTORE_TYPE is not defined")

    if TRIPLESTORE_HOST == None:
        raise Exception("Parameter TRIPLESTORE_HOST is not defined")
    
    if TRIPLESTORE_PORT == None:
        raise Exception("Parameter TRIPLESTORE_PORT is not defined")


    ## Check if triplestore type is supported
    if TRIPLESTORE_TYPE not in __supported_backend:
        raise Exception("The specified triplestore is not supported")


    print("Configuration loaded correctly!")


def inject_configuration(triplestore_host, triplestore_port, triplestore_type):
    global TRIPLESTORE_HOST,TRIPLESTORE_PORT,TRIPLESTORE_TYPE

    TRIPLESTORE_HOST = triplestore_host
    TRIPLESTORE_PORT = triplestore_port
    TRIPLESTORE_TYPE = triplestore_type
