"""
    Router for operations with the namespaces of a database
    It is an extension of the databases route
"""

from app.logger.logger import log
from typing import List

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from stardog.exceptions import StardogException # type: ignore


from pydantic import BaseModel

from tripper import Triplestore

from app.config.triplestoreConfig import TriplestoreConfig
from app.config.ontokbCredentials import OntoKBCredentials

from app.ontotrans_api.triplestore_instances import triplestore_insts as triplestore_instances



router = APIRouter(
    tags = ["Namespaces"]
)

triplestore_config = TriplestoreConfig()
ontokbcredentials_config = OntoKBCredentials()


def __get_triplestore_instance(db_name: str):
    if triplestore_instances.get_instance(db_name) is None:
        log.info("Creating new triplestore instance for database {}".format(db_name))
        triplestore = Triplestore(backend=triplestore_config.BACKEND, database=db_name, uname=ontokbcredentials_config.USERNAME, pwd=ontokbcredentials_config.PASSWORD)
        triplestore_instances.add_instance(db_name, triplestore)
   
    return triplestore_instances.get_instance(db_name)

#
# GET /databases/{db_name}/namespaces
#

### Model
class Namespace(BaseModel):
    prefix: str = ""
    iri: str = ""

class Namespaces(BaseModel):
    namespaces: List[Namespace] = []

### Route
@router.get("/databases/{db_name}/namespaces", response_model=Namespaces, status_code = status.HTTP_200_OK)
async def get_namespaces(db_name: str):
    """
        Retrieve the namespaces in a database
    """
    
    response = Namespaces()
    try:
        log.info("[DEBUG] - Using URL {}".format("http://{}:{}".format(triplestore_config.HOST, triplestore_config.PORT)))
        triplestore = __get_triplestore_instance(db_name)

        namespaces_raw = triplestore.backend.namespaces()
        namespaces = [Namespace(prefix=prefix, iri=iri) for (prefix, iri) in namespaces_raw.items()]
       
        response = Namespaces(namespaces=namespaces)

    except StardogException as err:
        log.error("Exception occurred in /namespaces: {}".format(err))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Database does not exist")

    except Exception as err:
        log.error("Exception occurred in /namespaces: {}".format(err))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cannot connect to Stardog instance")

    return response


#
# GET /databases/{db_name}/namespaces/base
#

### Route
@router.get("/databases/{db_name}/namespaces/base", response_model=Namespace, status_code = status.HTTP_200_OK, responses={404:{}})
async def get_base_namespace(db_name: str):
    """
        Retrieve the base namespace in a database
    """

    response = Namespace()
    try:
        
        triplestore = __get_triplestore_instance(db_name)


        namespaces_raw = triplestore.backend.namespaces()
        if "" in namespaces_raw:
            response = Namespace(prefix="base", iri=namespaces_raw[""])
        else:
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": "Base namespace does not exists"})
        
    except StardogException as err:
        log.error("Exception occurred in /namespaces/base: {}".format(err))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Database does not exist")
    
    except Exception as err:
        log.error("Exception occurred in /namespaces/base: {}".format(err))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cannot connect to Stardog instance")
        
    return response

#
# GET /databases/{db_name}/namespaces/{namespace_name}
#

### Route
@router.get("/databases/{db_name}/namespaces/{namespace_name}", response_model=Namespace, status_code = status.HTTP_200_OK, responses={404:{}})
async def get_namespace(db_name: str, namespace_name: str):
    """
        Retrieve a namespace in a database
    """

    response = Namespace()
    try:
        triplestore = __get_triplestore_instance(db_name)

        namespaces_raw = triplestore.backend.namespaces()
        if namespace_name in namespaces_raw:
            response = Namespace(prefix=namespace_name, iri=namespaces_raw[""])
        else:
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": "Namespace {} does not exists".format(namespace_name)})
        
    except StardogException as err:
        log.error("Exception occurred in /namespaces/{}: {}".format(namespace_name, err))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Database does not exist")
    
    except Exception as err:
        log.error("Exception occurred in /namespaces/{}: {}".format(namespace_name,err))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cannot connect to Stardog instance")
        
    return response

#
# POST /databases/{db_name}/namespaces
#

### Route
@router.post("/databases/{db_name}/namespaces", response_model=Namespace, status_code = status.HTTP_201_CREATED, responses={409:{}})
async def add_namespace(db_name: str, namespace: Namespace):
    """
        Add a new namespace in a database
    """

    real_prefix = "" if namespace.prefix == "base" else namespace.prefix
    real_namespace = Namespace(prefix=real_prefix, iri=namespace.iri)
    try:
        triplestore = __get_triplestore_instance(db_name)
        namespaces_raw = triplestore.backend.namespaces()

        if real_namespace.prefix in namespaces_raw and real_namespace.iri != namespaces_raw[real_namespace.prefix]:
            return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": "Already existing namespace"})

        triplestore.bind(real_namespace.prefix, real_namespace.iri)

    except StardogException as err:
        log.error("Exception occurred in /namespaces: {}".format(err))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Database does not exist")

    except Exception as err:
        log.error("Exception occurred in /namespaces: {}".format(err))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="{}".format(err))

    return real_namespace

#
# DELETE /databases/{db_name}/namespaces/base
#

### Model
class GenericBooleanResponse(BaseModel):
    response: bool

### Route
@router.delete("/databases/{db_name}/namespaces/base", status_code = status.HTTP_204_NO_CONTENT)
async def delete_namespace_byname(db_name: str):
    """
        Delete namespace in a database
    """

    try:
        triplestore = __get_triplestore_instance(db_name)
        namespaces_raw = triplestore.backend.namespaces()

        if "" in namespaces_raw:
            triplestore.backend.bind("", None) # type: ignore

    except StardogException as err:
        log.error("Exception occurred in /namespaces/base: {}".format(db_name,err))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Database does not exist")

    except Exception as err:
        log.error("Exception occurred in /namespaces/base: {}".format(db_name,err))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="{}".format(err))

#
# DELETE /databases/{db_name}/namespaces/{namespace_name}
#


### Route
@router.delete("/databases/{db_name}/namespaces/{namespace_name}", status_code = status.HTTP_204_NO_CONTENT)
async def delete_namespace(db_name: str, namespace_name: str):
    """
        Delete namespace in a database
    """

    try:
        triplestore = __get_triplestore_instance(db_name)
        namespaces_raw = triplestore.backend.namespaces()

        if namespace_name in namespaces_raw:
            triplestore.bind(namespace_name, None) # type: ignore

    except StardogException as err:
        log.error("Exception occurred in /namespaces/{}: {}".format(namespace_name, err))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Database does not exist")

    except Exception as err:
        log.error("Exception occurred in /namespaces/{}: {}".format(namespace_name, err))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="{}".format(err))