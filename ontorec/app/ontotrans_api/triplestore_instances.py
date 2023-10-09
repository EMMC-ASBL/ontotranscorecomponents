from tripper import Triplestore

class TriplestoreInstances():

    def __init__(self):
        self.instances = {}

    def add_instance(self, db_name: str, instance: Triplestore):
        self.instances[db_name] = instance

    def get_instance(self, db_name: str) -> Triplestore:
        return self.instances[db_name] if db_name in self.instances else None #type: ignore
    


triplestore_insts = TriplestoreInstances()