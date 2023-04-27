from pydantic import BaseSettings

class OntoKBCredentials(BaseSettings):

    ONTOKB_USERNAME: str = 'admin'
    ONTOKB_PASSWORD: str = 'admin'