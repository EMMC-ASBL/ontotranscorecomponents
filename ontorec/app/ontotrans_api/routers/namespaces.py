"""
    Router for operations with the namespaces of a database
    It is an extension of the databases route
"""

import os
import shutil
import stardog # type: ignore

from typing import List, Optional, Union

from fastapi.params import Body
from fastapi import File, UploadFile, Response
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from pydantic import BaseModel


from stardog.exceptions import StardogException # type: ignore

from ..core import connection_details

router = APIRouter(
    tags = ["Namespaces"]
)

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

    namespaces = []
    response = Namespaces()
    try:
        with stardog.Admin(**connection_details) as admin:
            database_instance = admin.database(db_name)
            namespaces = [Namespace(prefix=el["prefix"], iri=el["name"]) for el in database_instance.namespaces()]
            
        response.namespaces = namespaces

    except Exception as err:
        print("Exception occurred in /namespaces: {}".format(err))
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

    namespace = {}
    try:
        with stardog.Admin(**connection_details) as admin:
            database_instance = admin.database(db_name)
            namespace_list = list(filter(lambda x: x["prefix"]=="", database_instance.namespaces()))
            if len(namespace_list) > 0:
                namespace = namespace_list[0]
            else:
                return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": "Base namespace does not exists"})
    
    except Exception as err:
        print("Exception occurred in /namespaces/base: {}".format(err))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cannot connect to Stardog instance")
        
    return Namespace(prefix=namespace["prefix"], iri=namespace["name"])

#
# GET /databases/{db_name}/namespaces/{namespace_name}
#

### Route
@router.get("/databases/{db_name}/namespaces/{namespace_name}", response_model=Namespace, status_code = status.HTTP_200_OK, responses={404:{}})
async def get_namespace(db_name: str, namespace_name: str):
    """
        Retrieve a namespace in a database
    """

    namespace = {}
    try:
        with stardog.Admin(**connection_details) as admin:
            database_instance = admin.database(db_name)
            namespace_list = list(filter(lambda x: x["prefix"]==namespace_name, database_instance.namespaces()))
            if len(namespace_list) > 0:
                namespace = namespace_list[0]
            else:
                return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": "Namespace does not exists"})

    except Exception as err:
        print("Exception occurred in /namespaces/{}: {}".format(namespace_name, err))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cannot connect to Stardog instance")

    return Namespace(prefix=namespace["prefix"], iri=namespace["name"])

#
# POST /databases/{db_name}/namespaces
#

### Route
@router.post("/databases/{db_name}/namespaces", response_model=Namespace, status_code = status.HTTP_201_CREATED, responses={409:{}})
async def add_namespace(db_name: str, namespace: Namespace):
    """
        Add a new namespace in a database
    """

    true_prefix = "" if namespace.prefix == "base" else namespace.prefix
    true_namespace = Namespace(prefix=true_prefix, iri=namespace.iri)
    try:
        with stardog.Admin(**connection_details) as admin:
            database_instance = admin.database(db_name)
            matching_namespaces = list(filter(lambda x: x["prefix"]==true_namespace.prefix,database_instance.namespaces()))
            if len(matching_namespaces)>0:
                return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": "Already existing namespace"})
            else:
                database_instance.add_namespace(true_namespace.prefix, true_namespace.iri)

    except Exception as err:
        print("Exception occurred in /namespaces: {}".format(db_name,err))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="{}".format(err))

    return true_namespace

#
# DELETE /databases/{db_name}/namespaces/base
#

### Model
class GenericBooleanResponse(BaseModel):
    response: bool

### Route
@router.delete("/databases/{db_name}/namespaces/base", status_code = status.HTTP_204_NO_CONTENT)
async def delete_namespace(db_name: str):
    """
        Delete namespace in a database
    """

    namespace = {}
    response = False
    try:
        with stardog.Admin(**connection_details) as admin:
            database_instance = admin.database(db_name)
            matching_namespaces = list(filter(lambda x: x["prefix"]=="",database_instance.namespaces()))
            if len(matching_namespaces)>0:
                database_instance.remove_namespace("")

    except Exception as err:
        print("Exception occurred in /namespaces/base: {}".format(db_name,err))
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

    namespace = {}
    response = False
    try:
        with stardog.Admin(**connection_details) as admin:
            database_instance = admin.database(db_name)
            matching_namespaces = list(filter(lambda x: x["prefix"]==namespace_name,database_instance.namespaces()))
            if len(matching_namespaces)>0:
                database_instance.remove_namespace(namespace_name)

    except Exception as err:
        print("Exception occurred in /namespaces/{}: {}".format(namespace_name, err))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="{}".format(err))