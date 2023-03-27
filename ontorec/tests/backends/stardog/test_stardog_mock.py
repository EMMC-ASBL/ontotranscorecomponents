import sys
sys.path.append(".\\ontorec")
import os
import stardog
import rdflib
from pathlib import Path
print(sys.path)
# sys.path.append(".\\ontorec\\app")


from app.backends.stardog import StardogStrategy

if __name__ == "__main__":

    triple_1 = ("owl:Socrate", "owl:essere", "owl:Uomo")
    triple_2 = ("owl:Uomo", "owl:essere", "owl:mortale")
    triple_3 = ("owl:Socrate", "owl:essere", "owl:mortale")

    
    # triplestore = Triplestore(backend="stardog", base_iri="http://localhost:5820", database="pippodb")
    strategy = StardogStrategy(base_iri="http://localhost:5820", database="pippodb")


    # path = Path(os.path.abspath(r".\ontorec\tests\ontologies\family.ttl")).as_uri()
    # print(path)
    # print(Path(__file__))
    # path = str(Path(str(Path(__file__).parent.parent.resolve()) + "\\ontologies\\family.ttl"))
    # print(path)

    # print("1)", rdflib.URIRef("http://onto-ns.com/ontologies/examples/food#FOOD_e9cb271c_3be0_44e4_960f_6f6676445dbb"))
    # print("2)", rdflib.URIRef("http://onto-ns.com/ontologies/examples/food#FOOD_e9cb271c_3be0_44e4_960f_6f6676445dbb").n3())
    # print("3)", rdflib.URIRef("<http://onto-ns.com/ontologies/examples/food#FOOD_e9cb271c_3be0_44e4_960f_6f6676445dbb>"))
    # print("4)", rdflib.URIRef("<http://onto-ns.com/ontologies/examples/food#FOOD_e9cb271c_3be0_44e4_960f_6f6676445dbb>").n3())


    # backup = strategy.serialize()

    # databases = StardogStrategy.list_databases()
    # print(databases)

    remove_res = StardogStrategy.remove_database("pippodb")
    print(remove_res)
    
    create_res = StardogStrategy.create_database("pippodb")
    print(create_res)

    print(strategy.namespaces())

    print(strategy.bind("owl", None)) # type: ignore

    print(strategy.namespaces())

    # # add_res = strategy.add_triples([triple_4])
    # # print(add_res)
    

    # __connection_details = {
    #     'endpoint': "http://localhost:5820",
    #     'username': "admin",
    #     'password': "admin"
    # }
    # triple_4 = ("<http://onto-ns.com/ontologies/examples/food#FOOD_e9cb271c_3be0_44e4_960f_6f6676445dbb>", "rdf:type", "owl:Class")
    # triple_5 = ("<http://onto-ns.com/ontologies/examples/food#FOOD_e9cb271c_3be0_44e4_960f_6f6676445dbb>", "rdfs:subClassOf","<http://onto-ns.com/ontologies/examples/food#FOOD_d2741ae5_f200_4873_8f72_ac315917c41b>")
    # triple_6 = ("<http://onto-ns.com/ontologies/examples/food#FOOD_e9cb271c_3be0_44e4_960f_6f6676445dbb>", "<http://www.w3.org/2004/02/skos/core#prefLabel>", "\"Carrot\"@en")
    # __connection = stardog.Connection("pippodb", **__connection_details)
    # __connection.begin()
    # __connection.add(stardog.content.Raw("{} {} {}".format(*triple_4), "text/turtle"))
    # __connection.add(stardog.content.Raw("{} {} {}".format(*triple_5), "text/turtle"))
    # __connection.add(stardog.content.Raw("{} {} {}".format(*triple_6), "text/turtle"))
    # __connection.commit()

    # triples_set_2 = list(strategy.triples(("<http://onto-ns.com/ontologies/examples/food#FOOD_e9cb271c_3be0_44e4_960f_6f6676445dbb>", None, "<http://www.w3.org/2002/07/owl#Class>"))) # type: ignore
    # print(triples_set_2)

    ## GENERAL
    ## Problema: Non basta un solo endpoint per fare sia operazioni di query che update

    ## REMOVE
    ## Problema: non viene inserita la clausola where

    ## TRIPLES
    ## Primo problema: quando tutte le variabili sono definite non viene messo * nella clausola SELECT

    # list_triples = strategy.triples((None, "owl:essere", None)) # type: ignore
    # for el in list_triples:
    #     print(el)


    # ## Query
    # query_res = strategy.query(query_object="select * {?s ?p ?o}", reasoning=False)
    # print(query_res)

    # print(strategy.namespaces())

    # print(strategy.bind("msi", "http://msi.com/monitor#monitor"))

    # print(strategy.namespaces())

    # print(strategy.bind("msi", "http://msi.com/monitor#monitor"))

    # print(strategy.namespaces())

    # print(strategy.serialize())

    # # print(strategy.parse(data=backup))
    # add_res = strategy.remove(triple_1)
    # print(add_res)

    # print(strategy.serialize())
