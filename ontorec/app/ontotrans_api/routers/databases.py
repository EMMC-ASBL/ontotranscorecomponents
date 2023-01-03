"""
    Router for operations with databases
"""

import os
import app.ontotrans_api.handlers.triplestore_configuration as config

from pathlib import Path
from typing import List, Optional, Union, Tuple
from fastapi.params import Body
from fastapi import File, UploadFile, Response
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from pydantic import BaseModel

from tripper import Literal
from app.backends.stardog import StardogStrategy
from stardog.exceptions import StardogException # type: ignore


N3Triple = Tuple[str, str, str]

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
        databases = StardogStrategy.list_databases()

    except Exception as err:
        print("Exception occurred in /databases: {}".format(err))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cannot connect to Stardog instance")

    return Databases(dbs = databases)

#
#   GET /databases/{db_name}
#

### Model
class OntologyData(BaseModel):
    triples: List[N3Triple] = []

### Route
@router.get("/databases/{db_name}", response_model=OntologyData, status_code = status.HTTP_200_OK, responses={500: {}})
async def get_database_data(db_name: str):
    """
        Retrieve all data from a specific database
    """
    triples = []

    try:   
        triplestore = StardogStrategy(base_iri="http://{}:{}".format(config.TRIPLESTORE_HOST, config.TRIPLESTORE_PORT), database=db_name)
        db_content = triplestore.triples((None, None, None)) # type: ignore

        for triple in db_content:
            converted_triple = convert_triple_to_N3(triple) # type: ignore
            triples.append(converted_triple)

    except Exception as err:
        print("Exception occurred in /databases/{}: {}".format(db_name,err))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cannot connect to Stardog instance")

    return OntologyData(triples = triples) # type: ignore

#
# GET /databases/{db_name}/serialization
#

### Model
class SerializedContent(BaseModel):
    content: str = ""

@router.get("/databases/{db_name}/serialization", response_model=SerializedContent, status_code = status.HTTP_200_OK)
async def serialize_database(db_name:str, format: str = "turtle"):
    """
        Serialize database in a specific format
    """

    if format != "turtle":
        return JSONResponse(status_code=status.HTTP_406_NOT_ACCEPTABLE, content={"detail": "{} format not supported".format(format)})

    serialized_content = ""
    try:   
        triplestore = StardogStrategy(base_iri="http://{}:{}".format(config.TRIPLESTORE_HOST, config.TRIPLESTORE_PORT), database=db_name)
        serialized_content = triplestore.serialize(format="turtle")

    except Exception as err:
        print("Exception occurred in /databases/{}/serialization: {}".format(db_name,err))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cannot connect to Stardog instance")

    return SerializedContent(content=serialized_content)

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

    try:

        triplestore = StardogStrategy(base_iri="http://{}:{}".format(config.TRIPLESTORE_HOST, config.TRIPLESTORE_PORT), database=db_name)
        results = triplestore.query(queryModel.query, reasoning=queryModel.reasoning)

        triples = []
        for triple in results:
            converted_tuple = ()
            for el in triple:
                converted_tuple = converted_tuple + (convert_value_to_N3(el),)
            triples.append(converted_tuple)

    except Exception as err:
        print("Exception occurred in /databases/{}: {}".format(db_name,err))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cannot connect to Stardog instance")

    return triples # type: ignore


#
# POST /databases/{db_name}/create
#

### Model
class DatabaseGenericResponse(BaseModel):
    response: str = ""

### Route
@router.post("/databases/{db_name}/create", response_model=DatabaseGenericResponse, status_code = status.HTTP_201_CREATED)
async def create_database(db_name: str, initEmmo: Optional[bool] = True):
    """
       Create a database
    """

    try:

        current_databases = StardogStrategy.list_databases()
        if not db_name in current_databases: #type:ignore
            StardogStrategy.create_database(db_name)
        else:
            return JSONResponse(status_code=status.HTTP_409_CONFLICT, content="Database already exists")

        if initEmmo:
            triplestore = StardogStrategy(base_iri="http://{}:{}".format(config.TRIPLESTORE_HOST, config.TRIPLESTORE_PORT), database=db_name)
            emmo_path = str(Path(str(Path(__file__).parent.parent.parent.parent.resolve()) + os.path.sep.join(["", "ontologies","full_ontology_inferred_remapped.rdf"])))
            triplestore.parse(location=emmo_path, format="rdf")

    except Exception as err:
        print("Exception occurred in /databases/{}: {}".format(db_name,err))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cannot connect to Stardog instance")

    return DatabaseGenericResponse(response="Database created")

#
# POST /databases/{db_name}
#

### Model
class OntologyPostResponse(BaseModel):
    filename: Union[str, None] = None
    
### Route
@router.post("/databases/{db_name}", response_model=OntologyPostResponse, status_code = status.HTTP_200_OK)
async def add_data_to_database(db_name: str, response: Response,  ontology: UploadFile = File(...)):
    """
        Add an ontology file to the database
    """
    content = ontology.file.read()

    try:
        extension = ontology.filename.split(".")[1]
        if not extension in ["ttl"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Format {} not supported".format(extension))
        else:
            triplestore = StardogStrategy(base_iri="http://{}:{}".format(config.TRIPLESTORE_HOST, config.TRIPLESTORE_PORT), database=db_name)
            triplestore.parse(data=content)
    
    except Exception as err:
        print("Exception occurred in /databases/{}: {}".format(db_name,err))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cannot connect to Stardog instance")

    return OntologyPostResponse(filename=ontology.filename)

#
# POST /databases/{db_name}/single
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

        triplestore = StardogStrategy(base_iri="http://{}:{}".format(config.TRIPLESTORE_HOST, config.TRIPLESTORE_PORT), database=db_name)
        formatted_triples = []
        for triple in triples.triples:
            formatted_triples.append((triple.s, triple.p, triple.o))

        triplestore.add_triples(formatted_triples)
    
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

       StardogStrategy.remove_database(db_name)

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

        triplestore = StardogStrategy(base_iri="http://{}:{}".format(config.TRIPLESTORE_HOST, config.TRIPLESTORE_PORT), database=db_name)
        for triple in triples.triples:
            formatted_triple = (triple.s, triple.p, triple.o)
            triplestore.remove(formatted_triple) #type:ignore

    except Exception as err:
        print("Exception occurred in /databases/{}: {}".format(db_name,err))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cannot connect to Stardog instance")

    return DatabaseGenericResponse(response="Triples deleted successfully")


## Utils
def convert_value_to_N3(value):
    new_value = value.n3() if isinstance(value, Literal) else value if value.startswith("<") or value.startswith("_:") else "<{}>".format(value)  

    return new_value

def convert_triple_to_N3(triple):
    s, p, o = triple

    return (convert_value_to_N3(s), convert_value_to_N3(p), convert_value_to_N3(o))