from pydantic import BaseSettings
from pydantic import Field

class OntoRECSetting(BaseSettings):

    LOG_LEVEL: str = Field(
        'INFO',
        description="""
        Log Level for OntoREC service
        """
    )

    AUTHENTICATION_DEPENDENCIES: str = Field(
        "", description="List of FastAPI dependencies for authentication features."
    )


    class Config:
        env_prefix = "ONTOREC_"