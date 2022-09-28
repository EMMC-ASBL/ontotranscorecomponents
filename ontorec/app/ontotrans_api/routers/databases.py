"""
    Router for operations with databases
"""

import os
import shutil
import stardog # type: ignore

from typing import List, Optional, Union

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
            myres = conn.select(queryModel.query, reasoning = queryModel.reasoning)
            
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
class DatabaseGenericResponse(BaseModel):
    response: str = None

### Route
@router.post("/databases/{db_name}/create", response_model=DatabaseGenericResponse, status_code = status.HTTP_201_CREATED)
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

    return DatabaseGenericResponse(response="Database created")

#
# POST /databases/{db_name}/insert
#

### Model
class OntologyPostResponse(BaseModel):
    filename: str = None
    
### Route
@router.post("/databases/{db_name}", response_model=OntologyPostResponse, status_code = status.HTTP_200_OK)
async def add_data_to_database(db_name: str, response: Response,  ontology: UploadFile = File(...)):
    """
        Add an ontology file to the database
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

#
# POST /databases/{db_name}/insert/single
#

### Model
class Triple(BaseModel):
    s: Union[str, None]
    p: Union[str, None]
    o: Union[str, None]

class TripleList(BaseModel):
    triples: List[Triple]

    
### Route
@router.post("/databases/{db_name}/single", response_model=DatabaseGenericResponse, status_code = status.HTTP_200_OK)
async def add_triples_to_database(db_name: str, response: Response,  triples: TripleList):
    """
        Add single turtle triples to the database
    """

    try:

        with stardog.Admin(**connection_details) as admin:
            with stardog.Connection(db_name, **connection_details) as conn:
                conn.begin()

                for triple in triples.triples:
                    s = triple.s
                    p = triple.p
                    o = triple.o
                    
                    # Check if triple is complete - no handling if triple contains not defined namespaces
                    if s is not None and p is not None and o is not None:
                        conn.add(stardog.content.Raw("{} {} {}".format(s, p, o), "text/turtle"))
                
                conn.commit()

    except HTTPException as err:
        raise err

    except StardogException as err:
        print("Exception occurred in /databases/{}: {}".format(db_name,err))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error during processing of triples")
    
    except Exception as err:
        print("Exception occurred in /databases/{}: {}".format(db_name,err))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cannot connect to Stardog instance")

    return DatabaseGenericResponse(response="Triples added successfully")

#
# DELETE /databases/{db_name}
#

### Route
@router.delete("/databases/{db_name}", response_model = DatabaseGenericResponse, status_code = status.HTTP_200_OK)
async def delete_database(db_name: str):
    """
       Delete a database
    """
    try:

        with stardog.Admin(**connection_details) as admin:
            databases = list(map(lambda x : x.name ,admin.databases()))
            if not db_name in databases: 
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Database doesn't exists")

            with stardog.Connection(db_name, **connection_details) as conn:
                admin.database(db_name).drop()
    
    except HTTPException as err:
        raise err

    except Exception as err:
        print("Exception occurred in /databases/{}: {}".format(db_name,err))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cannot connect to Stardog instance")

    return DatabaseGenericResponse(response="Database deleted")

#
# DELETE /databases/{db_name}/single
#

### Route
@router.delete("/databases/{db_name}/single", response_model = DatabaseGenericResponse, status_code = status.HTTP_200_OK)
async def delete_database_triples(db_name: str,  triples: TripleList):
    """
       Delete triples from database
    """
    try:

        with stardog.Admin(**connection_details) as admin:
            with stardog.Connection(db_name, **connection_details) as conn:
                conn.begin()

                for triple in triples.triples:
                    s = triple.s
                    p = triple.p
                    o = triple.o
                    
                    # Check if triple is complete - no handling if triple contains not defined namespaces
                    if s is not None and p is not None and o is not None:
                        conn.remove(stardog.content.Raw("{} {} {}".format(s, p, o), "text/turtle"))
                
                conn.commit()
    
    except HTTPException as err:
        raise err

    except Exception as err:
        print("Exception occurred in /databases/{}: {}".format(db_name,err))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cannot connect to Stardog instance")

    return DatabaseGenericResponse(response="Triples deleted successfully")