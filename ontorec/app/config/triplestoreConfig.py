from pydantic import BaseSettings

class TriplestoreConfig(BaseSettings):

    ONTOKB_HOST: str = 'localhost'
    ONTOKB_PORT: str = '5820'
    ONTOKB_BACKEND: str = 'stardog'
    