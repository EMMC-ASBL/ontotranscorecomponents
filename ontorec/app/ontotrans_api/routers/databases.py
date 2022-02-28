"""
    Router for operations with databases
"""

import os
import shutil
import stardog # type: ignore

from typing import List, Optional

from fastapi.params import Body
from fastapi import File, UploadFile, Response
from fastapi import APIRouter, HTTPException, status

from pydantic import BaseModel

from stardog.exceptions import StardogException # type: ignore

from ..core import connection_details

router = APIRouter(
    tags = ["Databases"]
)

#
# GET /databases
#

### Model
class Databases(BaseModel):
    dbs: List[str] = []

### Route
@router.get("/databases", response_model=Databases, status_code = status.HTTP_200_OK)
async def get_databases():
    """
        Retrieve the list of databases
    """
    databases = []

    try:

        with stardog.Admin(**connection_details) as admin:
            databases = list(map(lambda x : x.name ,admin.databases()))

    except Exception as err:
        print("Exception occurred in /databases: {}".format(err))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cannot connect to Stardog instance")

    return Databases(dbs = databases)

#
#   GET /databases/{db_name}
#

### Model
class OntologyData(BaseModel):
    head: dict = {}
    results: dict = {}

### Route
@router.get("/databases/{db_name}", response_model=OntologyData, status_code = status.HTTP_200_OK, responses={404: {}, 500: {}})
async def get_database_data(db_name: str):
    """
        Retrieve all data from a specific database
    """
    ontology_data = ""

    try:   
        with stardog.Connection(db_name, **connection_details) as conn:
            query = "SELECT * where { ?s ?p ?o . }"
            ontology_data = conn.select(query)

    except StardogException as err:
        print("Exception occurred in /databases/{}: {}".format(db_name,err))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Database {} does not exists".format(db_name))

    except Exception as err:
        print("Exception occurred in /databases/{}: {}".format(db_name,err))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cannot connect to Stardog instance")

    return OntologyData(head = ontology_data["head"], results = ontology_data["results"])

#
# POST /databases/{db_name}/query
#

## Model
class QueryBody(BaseModel):
    query: str
    reasoning: Optional[bool] = False

### Route
@router.post("/databases/{db_name}/query", status_code = status.HTTP_200_OK, responses={400: {}, 500: {}})
async def execute_query(db_name: str, queryModel: QueryBody):
    """
        Execute a general query on a specific database
    """
    myres = ""

    try:

        with stardog.Connection(db_name, **connection_details) as conn:
            myres = conn.select(queryModel.query, variables={'@reasoning': queryModel.reasoning})
            
    except StardogException as err:
        print("Exception occurred in /databases/{}: {}".format(db_name,err))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error processing query")

    except Exception as err:
        print("Exception occurred in /databases/{}: {}".format(db_name,err))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cannot connect to Stardog instance")

    return myres


#
# POST /databases/{db_name}/create
#

### Model
class DatabaseCreationResponse(BaseModel):
    response: str = None

### Route
@router.post("/databases/{db_name}/create", response_model=DatabaseCreationResponse, status_code = status.HTTP_201_CREATED)
async def create_database(db_name: str, initEmmo: Optional[bool] = True):
    """
       Create a database
    """

    try:

        with stardog.Admin(**connection_details) as admin:
            databases = list(map(lambda x : x.name ,admin.databases()))
            if not db_name in databases: 
                database = admin.new_database(db_name)
            else:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Database already exists")

            if initEmmo:
                file = stardog.content.File("reasoner/ontology_cache/full_ontology_inferred_remapped.rdf")
                with stardog.Connection(db_name, **connection_details) as conn:
                    conn.begin()
                    conn.add(file)
                    conn.commit()
    
    except HTTPException as err:
        raise err

    except Exception as err:
        print("Exception occurred in /databases/{}: {}".format(db_name,err))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cannot connect to Stardog instance")

    return DatabaseCreationResponse(response="Database created")

#
# POST /databases/{db_name}
#

### Model
class OntologyPostResponse(BaseModel):
    filename: str = None
    
### Route
@router.post("/databases/{db_name}", response_model=OntologyPostResponse, status_code = status.HTTP_200_OK)
async def add_data_to_database(db_name: str, response: Response,  ontology: UploadFile = File(...)):
    """
        Add an ontology to the database
    """

    file_to_save = None

    if ontology is not None:
        extension = ontology.filename.split(".")[1]
        if not extension in ["rdf", "ttl"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Format {} not supported".format(extension))
        else:
            with open("tmp/" + ontology.filename, "wb") as buffer:
                shutil.copyfileobj(ontology.file, buffer)

        file_to_save = ontology.filename
        

    try:

        with stardog.Admin(**connection_details) as admin:
            file = stardog.content.File("tmp/{}".format(file_to_save))
            databases = list(map(lambda x : x.name ,admin.databases()))
            if not db_name in databases: 
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Database {} does not exists".format(db_name))
            with stardog.Connection(db_name, **connection_details) as conn:
                conn.begin()
                conn.add(file)
                conn.commit()

    except HTTPException as err:
        raise err

    except StardogException as err:
        print("Exception occurred in /databases/{}: {}".format(db_name,err))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error during processing of file")
    
    except Exception as err:
        print("Exception occurred in /databases/{}: {}".format(db_name,err))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cannot connect to Stardog instance")

    return OntologyPostResponse(filename=file_to_save)