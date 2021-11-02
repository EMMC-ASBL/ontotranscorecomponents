import requests


if __name__ == "__main__":
    response = requests.post(
        "http://localhost:8080/new/usecase",
        files={"ontology": (open(r"C:\Users\Alessandro\Desktop\Universita\Ricerca\OntoTrans\FactPlusPlus-1.2.0\emmo-inferred.rdf", "rb"))}
    )
    print(response.status_code)
    print(response.text)
