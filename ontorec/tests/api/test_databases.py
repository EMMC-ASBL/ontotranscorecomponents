import app
import os
import unittest
import stardog
import app.ontotrans_api.handlers.triplestore_configuration as config
from rdflib import BNode
from pathlib import Path
from rdflib import URIRef
from tripper.literal import Literal
from fastapi.testclient import TestClient


class NamespacesAPIs_TestCase(unittest.TestCase):

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
        self.__database_name = "database_test"
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

    def test_list_databases(self):
        response = self.__client.get("/databases/")
        response_obj = response.json()

        print(response_obj)
        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(response_obj["dbs"], self.__existing_databases + ["database_test"])


    def test_get_databases_content(self):
        triple_1 = [("<http://onto-ns.com/ontologies/examples/food#FOOD_e9cb271c_3be0_44e4_960f_6f6676445dbb>", "<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>", "<http://www.w3.org/2002/07/owl#Class>")]
        triple_2 = [("<http://onto-ns.com/ontologies/examples/food#FOOD_e9cb271c_3be0_44e4_960f_6f6676445dbb>", "<http://www.w3.org/2000/01/rdf-schema#subClassOf>","<http://onto-ns.com/ontologies/examples/food#FOOD_d2741ae5_f200_4873_8f72_ac315917c41b>")]
        triple_3 = [("<http://onto-ns.com/ontologies/examples/food#FOOD_e9cb271c_3be0_44e4_960f_6f6676445dbb>", "<http://www.w3.org/2004/02/skos/core#prefLabel>", "\"Carrot\"@en")]
        to_add = triple_1 + triple_2 + triple_3

        self.__connection.begin()
        for triple in to_add:
            self.__connection.add(stardog.content.Raw("{} {} {}".format(*triple), "text/turtle"))
        self.__connection.commit()

        response = self.__client.get("/databases/{}".format(self.__database_name))
        response_obj = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(response_obj["triples"], [ list(triple) for triple in to_add ])


    def test_serialize_turtle(self):
        ontology_file_path = str(Path(str(Path(__file__).parent.parent.resolve()) + os.path.sep.join(["","ontologies","food.ttl"])))
        self.__connection.begin()
        self.__connection.add(stardog.content.File(ontology_file_path))
        self.__connection.commit()

        response = self.__client.get("/databases/{}/serialization".format(self.__database_name))
        response_obj = response.json()
        db_content = response_obj["content"]

        with open(str(Path(str(Path(__file__).parent.parent.resolve()) + os.path.sep.join(["","ontologies","expected_ontology.ttl"]))), "r") as out_file:
            expected_serialization = out_file.read()
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(expected_serialization, db_content)


    def test_serialize_wrongformat(self):
        ontology_file_path = str(Path(str(Path(__file__).parent.parent.resolve()) + os.path.sep.join(["","ontologies","food.ttl"])))
        self.__connection.begin()
        self.__connection.add(stardog.content.File(ontology_file_path))
        self.__connection.commit()

        response = self.__client.get("/databases/{}/serialization?format=none".format(self.__database_name))
        
        self.assertEqual(response.status_code, 406)

    
    def test_query(self):
        ontology_file_path = str(Path(str(Path(__file__).parent.parent.resolve()) + os.path.sep.join(["","ontologies","food.ttl"])))
        self.__connection.begin()
        self.__connection.add(stardog.content.File(ontology_file_path))
        self.__connection.commit()

        query = {}
        query["query"] = """SELECT ?o WHERE { ?s <http://www.w3.org/2004/02/skos/core#prefLabel> "Fruit"@en .
  ?s1 <http://www.w3.org/2000/01/rdf-schema#subClassOf> ?s .
  ?s1 <http://www.w3.org/2004/02/skos/core#prefLabel> ?o . }"""
        query["reasoning"] = False

        response = self.__client.post("/databases/{}/query".format(self.__database_name), json=query)
        response_obj = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(response_obj, [['"Banana"@en'], ['"Orange"@en'], ['"Apple"@en']])


    def test_add_data(self):
        ontology_file_path = str(Path(str(Path(__file__).parent.parent.resolve()) + os.path.sep.join(["","ontologies","food.ttl"])))
        files = {'ontology': open(ontology_file_path,'r')}
        response = self.__client.post("/databases/{}".format(self.__database_name), files=files)
        response_obj = response.json()

        db_content = self.__connection.export(stardog.content_types.TURTLE).decode()  # type: ignore
        with open(str(Path(str(Path(__file__).parent.parent.resolve()) + os.path.sep.join(["","ontologies","expected_ontology.ttl"]))), "r") as out_file:
            expected_serialization = out_file.read()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_obj["filename"], "food.ttl")
        self.assertEqual(expected_serialization, db_content)


    def test_add_single_triples(self):
        triple_1 = [{"s":"<http://onto-ns.com/ontologies/examples/food#FOOD_e9cb271c_3be0_44e4_960f_6f6676445dbb>", "p":"<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>", "o":"<http://www.w3.org/2002/07/owl#Class>"}]
        triple_2 = [{"s":"<http://onto-ns.com/ontologies/examples/food#FOOD_e9cb271c_3be0_44e4_960f_6f6676445dbb>", "p":"<http://www.w3.org/2000/01/rdf-schema#subClassOf>","o":"<http://onto-ns.com/ontologies/examples/food#FOOD_d2741ae5_f200_4873_8f72_ac315917c41b>"}]
        triple_3 = [{"s":"<http://onto-ns.com/ontologies/examples/food#FOOD_e9cb271c_3be0_44e4_960f_6f6676445dbb>", "p":"<http://www.w3.org/2004/02/skos/core#prefLabel>", "o":"\"Carrot\"@en"}]
        to_add = triple_1 + triple_2 + triple_3
        triples_obj = {}
        triples_obj["triples"] = to_add

        response = self.__client.post("/databases/{}/single".format(self.__database_name), json=triples_obj)
        query_result = self.__connection.select("SELECT ?s ?p ?o WHERE { ?s ?p ?o . }", reasoning=False)
        triples = self.parseQueryResult(query_result) # type: ignore
        formatted_triples = []
        for triple in to_add:
            formatted_triples.append((triple["s"], triple["p"], triple["o"]))

        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(triples, formatted_triples)


    def test_delete_database(self):
        response = self.__client.delete("/databases/{}".format(self.__database_name))
        current_databases = list(map(lambda x : x.name ,  self.__admin.databases()))

        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(current_databases, self.__existing_databases)


    def test_delete_single_triples(self):
        triple_1 = [{"s":"<http://onto-ns.com/ontologies/examples/food#FOOD_e9cb271c_3be0_44e4_960f_6f6676445dbb>", "p":"<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>", "o":"<http://www.w3.org/2002/07/owl#Class>"}]
        triple_2 = [{"s":"<http://onto-ns.com/ontologies/examples/food#FOOD_e9cb271c_3be0_44e4_960f_6f6676445dbb>", "p":"<http://www.w3.org/2000/01/rdf-schema#subClassOf>","o":"<http://onto-ns.com/ontologies/examples/food#FOOD_d2741ae5_f200_4873_8f72_ac315917c41b>"}]
        triple_3 = [{"s":"<http://onto-ns.com/ontologies/examples/food#FOOD_e9cb271c_3be0_44e4_960f_6f6676445dbb>", "p":"<http://www.w3.org/2004/02/skos/core#prefLabel>", "o":"\"Carrot\"@en"}]
        to_add = triple_1 + triple_2 + triple_3
        formatted_triples = []
        for triple in to_add:
            formatted_triples.append((triple["s"], triple["p"], triple["o"]))

        self.__connection.begin()
        for triple in formatted_triples:
            self.__connection.add(stardog.content.Raw("{} {} {}".format(*triple), "text/turtle"))
        self.__connection.commit()

        triples_obj = {}
        triples_obj["triples"] = triple_1 + triple_3
        response = self.__client.delete("/databases/{}/single".format(self.__database_name), json=triples_obj)
        query_result = self.__connection.select("SELECT ?s ?p ?o WHERE { ?s ?p ?o . }", reasoning=False)
        triples = self.parseQueryResult(query_result) # type: ignore

        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(triples, formatted_triples[1:2])

    
    def test_create_database_wEmmo(self):
        marker = "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> ."
        db_name_to_create = "database_wemmo"
        response = self.__client.post("/databases/{}/create".format(db_name_to_create))

        new_connection = stardog.Connection(db_name_to_create, **self.__connection_details)
        db_content = new_connection.export(stardog.content_types.TURTLE).decode()  # type: ignore
        db_content = db_content[db_content.find(marker) + len(marker) :].strip()

        self.assertEqual(response.status_code, 201)
        self.assertTrue(db_content != "")


    def test_create_database_woEmmo(self):
        marker = "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> ."
        db_name_to_create = "database_woemmo"
        response = self.__client.post("/databases/{}/create?initEmmo=false".format(db_name_to_create))

        new_connection = stardog.Connection(db_name_to_create, **self.__connection_details)
        db_content = new_connection.export(stardog.content_types.TURTLE).decode()  # type: ignore
        db_content = db_content[db_content.find(marker) + len(marker) :].strip()

        self.assertEqual(response.status_code, 201)
        self.assertTrue(db_content == "")


    ## Utils functions
    def parseQueryResult(self, query_result: dict):
        query_vars = query_result["head"]["vars"]    # type: ignore
        query_bindings = query_result["results"]["bindings"]     # type: ignore

        triples_res = []
        for binding in query_bindings:
            current_triple = ()
            for var in query_vars:
                new_value = ""
                entry = binding[var]
                if entry["type"] == "uri":
                    new_value = entry["value"]
                elif entry["type"] == "literal":
                    new_value = Literal(
                        entry["value"],
                        lang=entry.get("xml:lang"),
                        datatype=entry.get("datatype"),
                    )
                elif entry["type"] == "bnode":
                    return (
                        entry["value"]
                        if entry["value"].startswith("_:")
                        else f"_:{entry['value']}"
                    )
                current_triple = current_triple + (new_value,)
            triples_res.append(self.normalizeTriple(current_triple))

        return triples_res

    def normalizeTriple(self, triple):
        converted_triple = ()
        for value in triple:
            converted_value = self.asuristr(value)
            converted_triple = converted_triple + (converted_value,)

        return converted_triple

    def normalizeTriples(self, triples):
        converted_triples = []
        for triple in triples:
            converted_triples.append(self.normalizeTriple(triple))

        return converted_triples

    def asuristr(self, value):
        if value is None:
            return None
        if isinstance(value, Literal):
            return value.n3()
        if value.startswith("_:"):
            return BNode(value).n3()
        if value.startswith("<"):
            value = value[1:-1]
        return URIRef(value).n3()