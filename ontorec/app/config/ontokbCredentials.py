from pydantic import BaseSettings
from pydantic import Field

class OntoKBCredentials(BaseSettings):

    USERNAME: str = Field(
        'admin',
        description="""
        Username to access the underlying OntoKB triplestore technology.
        WARNING: All the users will access with this same account.
        """
    )
    PASSWORD: str = Field(
        'admin',
        description="""Password to access the underlying OntoKB triplestore technology."""
    )

    class Config:
        env_prefix = "ONTOKB_"