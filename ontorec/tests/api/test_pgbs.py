import app
import os
import unittest
import stardog
import json
import app.ontotrans_api.handlers.triplestore_configuration as config
from rdflib import BNode
from pathlib import Path
from rdflib import URIRef
from tripper.literal import Literal
from fastapi.testclient import TestClient


class PGBSAPIs_TestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        cls.__client = TestClient(app.create_app())
        config.inject_configuration("localhost", "5820", "stardog")
        endpoint = "http://{}:{}".format(config.TRIPLESTORE_HOST, config.TRIPLESTORE_PORT)
        cls.__admin: stardog.Admin = stardog.Admin(endpoint = endpoint)
        cls.__existing_databases = list(map(lambda x : x.name ,  cls.__admin.databases()))
        cls.__connection_details = {
            'endpoint': endpoint,
            'username': "admin",
            'password': "admin"
        }

    def setUp(self):

        self.maxDiff = None
        self.__database_name = "pgbs_test"
        self.__database = self.__admin.new_database(self.__database_name)
        self.__connection = stardog.Connection(self.__database_name, **self.__connection_details)
        self.__existing_namespaces = self.__database.namespaces() # type: ignore
        self.__existing_namespaces = [ {"prefix": namespace["prefix"], "iri": namespace["name"]} for namespace in self.__existing_namespaces]

    @classmethod
    def tearDownClass(cls):
        pass

    def tearDown(self):
        currently_existing_dbs = list(map(lambda x : x.name ,  self.__admin.databases()))
        newly_created_dbs = set(currently_existing_dbs) ^ set(self.__existing_databases)

        for db in newly_created_dbs:
            try:
                self.__admin.database(db).drop()
            except Exception as err:
                print("Database {} already deleted...skipping".format(db))


    ## Unit test

    def test_model_training_A(self):
        
        with open(str(Path(str(Path(__file__).parent.parent.resolve()) + os.path.sep.join(["","resources","pgbs", "model_training_A.json"]))), "r") as json_file:
            json_content = json.load(json_file)


        response = self.__client.post("/databases/{}/pgbs/model_training".format(self.__database_name), json=json_content)
        self.assertEqual(response.status_code, 201)



    def test_model_training_B(self):
        
        with open(str(Path(str(Path(__file__).parent.parent.resolve()) + os.path.sep.join(["","resources","pgbs", "model_training_B.json"]))), "r") as json_file:
            json_content = json.load(json_file)


        response = self.__client.post("/databases/{}/pgbs/model_training".format(self.__database_name), json=json_content)
        self.assertEqual(response.status_code, 201)


    def test_model_evaluation(self):
        
        with open(str(Path(str(Path(__file__).parent.parent.resolve()) + os.path.sep.join(["","resources","pgbs", "model_evaluation.json"]))), "r") as json_file:
            json_content = json.load(json_file)


        response = self.__client.post("/databases/{}/pgbs/model_evaluation".format(self.__database_name), json=json_content)
        self.assertEqual(response.status_code, 201)