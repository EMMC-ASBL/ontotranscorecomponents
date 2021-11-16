"""
    Router for operations with databases
"""

import shutil
import stardog # type: ignore

from typing import List

from fastapi.params import Body
from fastapi import File, UploadFile, Response
from fastapi import APIRouter, HTTPException, status

from stardog.exceptions import StardogException # type: ignore

from ..core import connection_details

router = APIRouter()

@router.get("/databases", status_code = status.HTTP_200_OK)
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

    return databases

@router.get("/databases/{db_name}", status_code = status.HTTP_200_OK)
async def get_database_data(db_name: str):
    """
        Retrieve all data from a specific database
    """
    myres = ""

    try:   
        with stardog.Connection(db_name, **connection_details) as conn:
            query = "SELECT * where { ?s ?p ?o . }"
            myres = conn.select(query)

    except StardogException as err:
        print("Exception occurred in /databases/{}: {}".format(db_name,err))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Database {} does not exists".format(db_name))

    except Exception as err:
        print("Exception occurred in /databases/{}: {}".format(db_name,err))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cannot connect to Stardog instance")

    return myres

@router.post("/databases/{db_name}/query", status_code = status.HTTP_200_OK)
async def execute_query(db_name: str, query: str = Body(..., embed = True)):
    """
        Execute a general query on a specific database
    """
    myres = ""

    try:

        with stardog.Connection(db_name, **connection_details) as conn:
            myres = conn.select(query)
            
    except StardogException as err:
        print("Exception occurred in /databases/{}: {}".format(db_name,err))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Error processing query")

    except Exception as err:
        print("Exception occurred in /databases/{}: {}".format(db_name,err))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cannot connect to Stardog instance")

    return myres
    
@router.post("/databases/{db_name}", status_code = status.HTTP_200_OK)
async def add_data_to_database(db_name: str, response: Response, ontology: UploadFile = File(None)):
    """
        Add an ontology to the database. Create the databases if it doesn't exists
    """

    database = None
    databases = []
    file_to_save = None

    if ontology is not None:
        extension = ontology.filename.split(".")[1]
        if not extension in ["rdf", "ttl"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Format {} not supported".format(extension))
        else:
            with open("tmp/" + ontology.filename, "wb") as buffer:
                shutil.copyfileobj(ontology.file, buffer)

        file_to_save = ontology.filename
    else:
        file_to_save = "full_ontology_inferred_remapped.rdf"
        

    try:

        with stardog.Admin(**connection_details) as admin:
            file = stardog.content.File("tmp/{}".format(file_to_save))
            databases = list(map(lambda x : x.name ,admin.databases()))
            if not db_name in databases: database = admin.new_database(db_name)
            with stardog.Connection(db_name, **connection_details) as conn:
                conn.begin()
                conn.add(file)
                conn.commit()

    except StardogException as err:
        print("Exception occurred in /databases/{}: {}".format(db_name,err))
        if database is not None: database.drop()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error during processing of file")
    
    except Exception as err:
        print("Exception occurred in /databases/{}: {}".format(db_name,err))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cannot connect to Stardog instance")

    if database is not None: response.status_code = status.HTTP_201_CREATED
    return {"filename": file_to_save}