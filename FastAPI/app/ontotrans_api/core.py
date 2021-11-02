"""
test apirouter
"""

import shutil
import subprocess # nosec
import stardog # type: ignore

from fastapi import APIRouter, File, UploadFile

router = APIRouter()

connection_details = {
    'endpoint': 'http://172.17.0.2:5820',
    'username': 'admin',
    'password': 'admin'
}

@router.get("/")
async def home():
    """
    Home endpoint
    """
    return {"msg": "OntoTrans FastAPI v0.1"}

@router.get("/all/{database_name}")
async def all_triples(database_name):
    """
    First true Stardog endpoint
    """

    myres=""

    with stardog.Connection(database_name, **connection_details) as conn:
        query = "SELECT * where { ?s ?p ?o . }"
        myres=conn.select(query)

    return myres

@router.get("/new/db/{db_name}")
async def add_db(db_name):
    """
    /DUMMY/ echo test DB endpoint
    """
    output = subprocess.run(["java", "--version"], capture_output=True, check=True) # nosec
    print (db_name)
    return {"db name": output}

@router.post("/new/usecase/")
async def up_ontology(ontology: UploadFile = File(...)):
    """
    upload endpoint
    """
    #pylint: disable=unused-variable

    extension = ontology.filename.split(".")[1]
    if extension in ["rdf", "ttl"]:
        with open("tmp/destination." + extension, "wb") as buffer:
            shutil.copyfileobj(ontology.file, buffer)
        # now we have the file saved on the server, we've to convert it and then send to Stardog

        with stardog.Admin(**connection_details) as admin:
            database = admin.new_database('database_test', {}, stardog.content.File("tmp/destination.rdf"))
            # with stardog.Connection('database', **connection_details) as conn:
            #     conn.begin()
            #     conn.add(stardog.content.File('destination.ttl'))
            #     conn.commit()
        return {"filename": ontology.filename}
    
    return {"error": "Format " + extension + " not supported"}

#    return {"PWD": os.getcwd(), "FILE": __file__, "cnt": content}
