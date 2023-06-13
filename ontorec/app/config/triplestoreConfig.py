from pydantic import BaseSettings
from pydantic import Field


class TriplestoreConfig(BaseSettings):

    HOST: str = Field(
        'localhost',
        description="""
        The IP address on which OntoKB is deployed.
        """
    )
    PORT: str = Field(
        '5820',
        description="""
        The port on which OntoKB is deployed.
        """
    )
    BACKEND: str = Field(
        'stardog',
        description="""
        The underlying technology (triplestore) used by OntoKB.
        Current supported ones comprises:
        * stardog
        """
    )

    class Config:
        env_prefix = "ONTOKB_"
    