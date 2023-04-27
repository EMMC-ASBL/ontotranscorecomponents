import app
import unittest
import stardog
from fastapi.testclient import TestClient

from app.config.triplestoreConfig import TriplestoreConfig

triplestore_config = TriplestoreConfig()


class NamespacesAPIs_TestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        cls.__client = TestClient(app.create_app())
        endpoint = "http://{}:{}".format(triplestore_config.ONTOKB_HOST, triplestore_config.ONTOKB_PORT)
        cls.__admin: stardog.Admin = stardog.Admin(endpoint = endpoint)
        cls.__existing_databases = list(map(lambda x : x.name ,  cls.__admin.databases()))
        cls.__connection_details = {
            'endpoint': endpoint,
            'username': "admin",
            'password': "admin"
        }

    def setUp(self):

        self.maxDiff = None
        self.__database_name = "namespace_test"
        self.__database = self.__admin.new_database(self.__database_name)
        self.__connection = stardog.Connection(self.__database_name, **self.__connection_details)
        self.__existing_namespaces = self.__database.namespaces() # type: ignore
        self.__existing_namespaces = [ {"prefix": namespace["prefix"], "iri": namespace["name"]} for namespace in self.__existing_namespaces]
        tripper_def_namespaces = {
            "xml": "http://www.w3.org/XML/1998/namespace",
            "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
            "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
            "xsd": "http://www.w3.org/2001/XMLSchema#",
            "owl": "http://www.w3.org/2002/07/owl#",
        }
        for def_namespace in tripper_def_namespaces.keys():
            if next((item for item in self.__existing_namespaces if item["prefix"] == def_namespace), None) is None:
                self.__existing_namespaces.append({"prefix":def_namespace, "iri": tripper_def_namespaces[def_namespace]})


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

    def test_list_namespaces(self):
        response = self.__client.get("/databases/{}/namespaces".format(self.__database_name))
        response_obj = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(response_obj["namespaces"], self.__existing_namespaces)


    def test_get_base_namespaces(self):
        response = self.__client.get("/databases/{}/namespaces/base".format(self.__database_name))
        response_obj = response.json()

        base_namespaces = {"prefix": "", "iri": "http://api.stardog.com/"}

        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(response_obj, base_namespaces)


    def test_get_base_namespaceser_error(self):

        self.__database.remove_namespace("") #type:ignore
        response = self.__client.get("/databases/{}/namespaces/base".format(self.__database_name))

        self.assertEqual(response.status_code, 404)


    def test_get_namespaces(self):
        response = self.__client.get("/databases/{}/namespaces/owl".format(self.__database_name))
        response_obj = response.json()

        target_namespaces = {"prefix": "owl", "iri": "http://www.w3.org/2002/07/owl#"}

        self.assertEqual(response.status_code, 200)
        self.assertTrue(target_namespaces, response_obj)


    def test_get_namespaceser_error(self):

        response = self.__client.get("/databases/{}/namespaces/nonamespace".format(self.__database_name))

        self.assertEqual(response.status_code, 404)


    def test_add_namespace(self):
        new_namespace = {}
        new_namespace["prefix"] = "food"
        new_namespace["iri"] = "http://onto-ns.com/ontologies/examples/food#"

        response = self.__client.post("/databases/{}/namespaces".format(self.__database_name), json=new_namespace)
        response_obj = response.json()
        updated_namespaces = self.__database.namespaces() # type: ignore
        updated_namespaces = [ {"prefix": namespace["prefix"], "iri": namespace["name"]} for namespace in updated_namespaces]

        self.assertEqual(response.status_code, 201)
        self.assertTrue(new_namespace, response_obj)
        self.assertCountEqual(updated_namespaces, self.__existing_namespaces + [new_namespace]) # type: ignore


    def test_add_base_namespace(self):
        new_base_namespace = {}
        new_base_namespace["prefix"] = "base"
        new_base_namespace["iri"] = "http://onto-ns.com/ontologies/examples/food#"

        old_base_namespace = {}
        old_base_namespace["prefix"] = ""
        old_base_namespace["iri"] = "http://api.stardog.com/"

        self.__database.remove_namespace("") #type:ignore

        response = self.__client.post("/databases/{}/namespaces".format(self.__database_name), json=new_base_namespace)
        response_obj = response.json()
        updated_namespaces = self.__database.namespaces() # type: ignore
        updated_namespaces = [ {"prefix": namespace["prefix"], "iri": namespace["name"]} for namespace in updated_namespaces]
        self.__existing_namespaces.remove(old_base_namespace)
        self.__existing_namespaces = self.__existing_namespaces + [{"prefix": "", "iri": new_base_namespace["iri"]}]

        self.assertEqual(response.status_code, 201)
        self.assertTrue(new_base_namespace, response_obj)
        self.assertCountEqual(updated_namespaces, self.__existing_namespaces) # type: ignore

    
    def test_add_namespace_conflict(self):
        new_namespace = {}
        new_namespace["prefix"] = "owl"
        new_namespace["iri"] = "http://onto-ns.com/ontologies/examples/food#"

        response = self.__client.post("/databases/{}/namespaces".format(self.__database_name), json=new_namespace)
        response_obj = response.json()
        updated_namespaces = self.__database.namespaces() # type: ignore
        updated_namespaces = [ {"prefix": namespace["prefix"], "iri": namespace["name"]} for namespace in updated_namespaces]

        self.assertEqual(response.status_code, 409)
        self.assertCountEqual(updated_namespaces, self.__existing_namespaces) # type: ignore


    def test_delete_base_namespace(self):
        # removed_namespace = {}
        # removed_namespace["prefix"] = ""
        # removed_namespace["iri"] = "http://www.w3.org/2002/07/owl#"

        # self.__database.remove_namespace("") # type: ignore
        # self.__database.remove_namespace("owl") # type: ignore
        # self.__database.add_namespace("", removed_namespace["iri"]) # type: ignore

        before_namespaces = self.__database.namespaces() # type: ignore
        response = self.__client.delete("/databases/{}/namespaces/base".format(self.__database_name))
        after_namespaces = self.__database.namespaces() # type: ignore
        # updated_namespaces = self.__database.namespaces() # type: ignore
        # updated_namespaces = [ {"prefix": namespace["prefix"], "iri": namespace["name"]} for namespace in updated_namespaces]
        # self.__existing_namespaces.remove(removed_namespace)

        self.assertEqual(response.status_code, 204)
        self.assertTrue(next((item for item in before_namespaces if item["prefix"] == ""), None) is not None)
        self.assertTrue(next((item for item in after_namespaces if item["prefix"] == ""), None) is None)
        # self.assertCountEqual(updated_namespaces, self.__existing_namespaces) # type: ignore


    def test_delete_base_namespace_ifnotexists(self):
        removed_namespace = {}
        removed_namespace["prefix"] = ""
        removed_namespace["iri"] = "http://api.stardog.com/"

        self.__database.remove_namespace("") #type:ignore

        response = self.__client.delete("/databases/{}/namespaces/base".format(self.__database_name))
        updated_namespaces = self.__database.namespaces() # type: ignore
        updated_namespaces = [ {"prefix": namespace["prefix"], "iri": namespace["name"]} for namespace in updated_namespaces]
        self.__existing_namespaces.remove(removed_namespace)

        self.assertEqual(response.status_code, 204)
        self.assertCountEqual(updated_namespaces, self.__existing_namespaces) # type: ignore


    def test_delete_namespace(self):
        removed_namespace = {}
        removed_namespace["prefix"] = "owl"
        removed_namespace["iri"] = "http://www.w3.org/2002/07/owl#"

        response = self.__client.delete("/databases/{}/namespaces/owl".format(self.__database_name))
        updated_namespaces = self.__database.namespaces() # type: ignore
        updated_namespaces = [ {"prefix": namespace["prefix"], "iri": namespace["name"]} for namespace in updated_namespaces]
        self.__existing_namespaces.remove(removed_namespace)

        self.assertEqual(response.status_code, 204)
        self.assertCountEqual(updated_namespaces, self.__existing_namespaces) # type: ignore

    def test_delete_namespace_ifnotexists(self):
        removed_namespace = {}
        removed_namespace["prefix"] = "owl"
        removed_namespace["iri"] = "http://www.w3.org/2002/07/owl#"

        self.__database.remove_namespace("owl") #type:ignore

        response = self.__client.delete("/databases/{}/namespaces/owl".format(self.__database_name))
        updated_namespaces = self.__database.namespaces() # type: ignore
        updated_namespaces = [ {"prefix": namespace["prefix"], "iri": namespace["name"]} for namespace in updated_namespaces]
        self.__existing_namespaces.remove(removed_namespace)

        self.assertEqual(response.status_code, 204)
        self.assertCountEqual(updated_namespaces, self.__existing_namespaces) # type: ignore



    ## Utils

    def __get_default_namespaces(self):

        return [
            {"prefix": "", "iri": "http://api.stardog.com/"},
            {"prefix": "owl", "iri": "http://www.w3.org/2002/07/owl#"},
            {"prefix": "rdf", "iri": "http://www.w3.org/1999/02/22-rdf-syntax-ns#"},
            {"prefix": "rdfs", "iri": "http://www.w3.org/2000/01/rdf-schema#"},
            {"prefix": "stardog", "iri": "tag:stardog:api:"},
            {"prefix": "xsd", "iri": "http://www.w3.org/2001/XMLSchema#"},
        ]
