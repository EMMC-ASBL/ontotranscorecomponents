"""
    Router for PGBS demo's specific routes
"""

import os
import uuid
import app.ontotrans_api.handlers.triplestore_configuration as config

from pathlib import Path
from typing import List, Optional, Union, Tuple
from fastapi.params import Body
from fastapi import File, UploadFile, Response
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from pydantic import BaseModel, Field

from tripper import Literal
from tripper.namespace import XSD
from app.backends.stardog import StardogStrategy
from stardog.exceptions import StardogException # type: ignore

from datetime import date, datetime

router = APIRouter(
    tags = ["PGBS"]
)

#
# POST /databases/{db_name}/pgbs/model_training
#

### Model
class Scenario(BaseModel):
    country: str
    brand: str
    jobs: str

class ReferencePeriod(BaseModel):
    from_: str = Field(alias="from")
    to_: str = Field(alias="to")

    class Config:
        allow_population_by_field_name = True

class PriceUnits(BaseModel):
    min: str
    max: str

class NumericalDistribution(BaseModel):
    min: str
    max: str

class ModelInputs(BaseModel):
    price_units: PriceUnits = Field(alias="Price per 100 pods (0-1 USD)")
    numerical_dist: NumericalDistribution = Field(alias="Numerical distribution (0-1)")

    class Config:
        allow_population_by_field_name = True

class Results(BaseModel):
    model_id: str
    model_quality: str
    data_rows: str
    creation_date: datetime
    model_inputs: ModelInputs

class ModelTraining(BaseModel):
    training_type: str
    gtin: Optional[str]
    scenario: Optional[Scenario]
    reference_period: Optional[ReferencePeriod]
    results: Results

class TraningModelResponse(BaseModel):
    model_training_uri: str
    training_results_uri: str


### Route
@router.post("/databases/{db_name}/pgbs/model_training", response_model=TraningModelResponse, status_code = status.HTTP_201_CREATED)
async def save_model_training(db_name: str, modelTraining: ModelTraining):
    """
        Save data related to model training
    """

    try:
        # Generate random ID for model training
        model_training_id = "{}-{}".format(modelTraining.training_type, uuid.uuid4())
        model_training_uri = "https://example.com/model_training/{}".format(model_training_id)
        training_results_uri = "https://example.com/training_results/{}".format(model_training_id)


        formatted_triples = []
        formatted_triples.append((model_training_uri, "<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>", "https://schema.org/ModelTraining"))
        formatted_triples.append((model_training_uri, "<https://schema.org/training_type>", "\"{}\"".format(modelTraining.training_type)))
        formatted_triples.append((model_training_uri, "<https://schema.org/results>", "\"{}\"".format(training_results_uri)))

        if modelTraining.gtin is not None:
            formatted_triples.append((model_training_uri, "<https://schema.org/gtin>", "<https://example.com/product/{}>".format(modelTraining.gtin)))

        if modelTraining.scenario is not None:
            formatted_triples.append((model_training_uri, "<https://schema.org/country>", "\"{}\"".format(modelTraining.scenario.country)))
            formatted_triples.append((model_training_uri, "<https://schema.org/brand>", "\"{}\"".format(modelTraining.scenario.brand)))
            formatted_triples.append((model_training_uri, "<https://schema.org/jobs>", Literal(modelTraining.scenario.jobs, datatype="<http://www.w3.org/2001/XMLSchema#integer>").n3())) # type: ignore

        if modelTraining.reference_period is not None:
            formatted_triples.append((model_training_uri, "<https://schema.org/from>", Literal(modelTraining.reference_period.from_, datatype="<http://www.w3.org/2001/XMLSchema#date>").n3())) # type: ignore
            formatted_triples.append((model_training_uri, "<https://schema.org/to>", Literal(modelTraining.reference_period.to_, datatype="<http://www.w3.org/2001/XMLSchema#date>").n3())) # type: ignore

        formatted_triples.append((training_results_uri, "<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>", "https://schema.org/TrainingResults"))
        formatted_triples.append((training_results_uri, "<https://schema.org/id>", "<https://example.com/model/{}>".format(modelTraining.results.model_id)))
        formatted_triples.append((training_results_uri, "<https://schema.org/quality>", Literal(modelTraining.results.model_quality, datatype="<http://www.w3.org/2001/XMLSchema#float>").n3())) # type: ignore
        formatted_triples.append((training_results_uri, "<https://schema.org/data_rows>", Literal(modelTraining.results.data_rows, datatype="<http://www.w3.org/2001/XMLSchema#integer>").n3())) # type: ignore
        formatted_triples.append((training_results_uri, "<https://schema.org/creation_date>", Literal(modelTraining.results.creation_date.strftime("%Y-%m-%dT%H:%M:%S"), datatype="<http://www.w3.org/2001/XMLSchema#dateTime>").n3())) # type: ignore
        formatted_triples.append((training_results_uri, "<https://schema.org/input_price_min>", Literal(modelTraining.results.model_inputs.price_units.min, datatype="<http://www.w3.org/2001/XMLSchema#float>").n3())) # type: ignore
        formatted_triples.append((training_results_uri, "<https://schema.org/input_price_max>", Literal(modelTraining.results.model_inputs.price_units.max, datatype="<http://www.w3.org/2001/XMLSchema#float>").n3())) # type: ignore
        formatted_triples.append((training_results_uri, "<https://schema.org/numerical_distribution_min>", Literal(modelTraining.results.model_inputs.numerical_dist.min, datatype="<http://www.w3.org/2001/XMLSchema#float>").n3())) # type: ignore
        formatted_triples.append((training_results_uri, "<https://schema.org/numerical_distribution_max>", Literal(modelTraining.results.model_inputs.numerical_dist.min, datatype="<http://www.w3.org/2001/XMLSchema#float>").n3())) # type: ignore


        # Save triples
        triplestore = StardogStrategy(base_iri="http://{}:{}".format(config.TRIPLESTORE_HOST, config.TRIPLESTORE_PORT), database=db_name)
        SCHEMA = triplestore.bind("schema", "https://schema.org/")
        triplestore.add_triples(formatted_triples)

    except Exception as err:
        print("Exception occurred in /databases/{}/pgbs/model_training: {}".format(db_name, err))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cannot connect to Stardog instance")

    return TraningModelResponse(model_training_uri = model_training_uri , training_results_uri = training_results_uri)



#
# POST /databases/{db_name}/pgbs/model_evaluation
#

### Model

class Prediction(BaseModel):
    predicted: List[float]
    uncertainty_min: List[float]
    uncertainty_max: List[float]
    model_based_outlier: List[float]
    price: List[float] = Field(alias="Price per 100 pods (0-1 USD)")
    num_dist: List[float] = Field(alias="Numerical distribution (0-1)")

    class Config:
        allow_population_by_field_name = True

class ModelInputsList(BaseModel):
    price_units: List[float] = Field(alias="Price per 100 pods (0-1 USD)")
    numerical_dist: List[float] = Field(alias="Numerical distribution (0-1)")

    class Config:
        allow_population_by_field_name = True

class ModelEvaluation(BaseModel):
    model_id: str
    model_inputs: ModelInputsList
    prediction: Prediction

class TraningEvaluationResponse(BaseModel):
    model_evaluation_uri: str
    


### Route
@router.post("/databases/{db_name}/pgbs/model_evaluation", response_model=TraningEvaluationResponse, status_code = status.HTTP_201_CREATED)
async def save_model_evaluation(db_name: str, modelEvalutaion: ModelEvaluation):
    """
        Save data related to model evaluation
    """

    try:
        # Generate random ID for model training
        model_training_id = modelEvalutaion.model_id
        model_evaluation_uri = "https://example.com/model_evaluation/{}".format(model_training_id)


        formatted_triples = []
        formatted_triples.append((model_evaluation_uri, "<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>", "https://schema.org/ModelEvaluation"))
        formatted_triples.append((model_evaluation_uri, "<https://schema.org/model_id>", "<https://example.com/model/{}>".format(modelEvalutaion.model_id)))
        formatted_triples.append((model_evaluation_uri, "<https://schema.org/input_price>", Literal(modelEvalutaion.model_inputs.price_units[0], datatype="<http://www.w3.org/2001/XMLSchema#float>").n3())) # type: ignore
        formatted_triples.append((model_evaluation_uri, "<https://schema.org/input_numerical_distribution>", Literal(modelEvalutaion.model_inputs.numerical_dist[0], datatype="<http://www.w3.org/2001/XMLSchema#float>").n3())) # type: ignore
        formatted_triples.append((model_evaluation_uri, "<https://schema.org/predicted>", Literal(modelEvalutaion.prediction.predicted[0], datatype="<http://www.w3.org/2001/XMLSchema#float>").n3())) # type: ignore
        formatted_triples.append((model_evaluation_uri, "<https://schema.org/uncertainty_min>", Literal(modelEvalutaion.prediction.uncertainty_min[0], datatype="<http://www.w3.org/2001/XMLSchema#float>").n3())) # type: ignore
        formatted_triples.append((model_evaluation_uri, "<https://schema.org/uncertainty_max>", Literal(modelEvalutaion.prediction.uncertainty_max[0], datatype="<http://www.w3.org/2001/XMLSchema#float>").n3())) # type: ignore
        formatted_triples.append((model_evaluation_uri, "<https://schema.org/model_based_outlier>", Literal(modelEvalutaion.prediction.model_based_outlier[0], datatype="<http://www.w3.org/2001/XMLSchema#float>").n3())) # type: ignore
        formatted_triples.append((model_evaluation_uri, "<https://schema.org/prediction_price>", Literal(modelEvalutaion.prediction.price[0], datatype="<http://www.w3.org/2001/XMLSchema#float>").n3())) # type: ignore
        formatted_triples.append((model_evaluation_uri, "<https://schema.org/prediction_numerical_distribution>", Literal(modelEvalutaion.prediction.num_dist[0], datatype="<http://www.w3.org/2001/XMLSchema#float>").n3())) # type: ignore

        # Save triples
        triplestore = StardogStrategy(base_iri="http://{}:{}".format(config.TRIPLESTORE_HOST, config.TRIPLESTORE_PORT), database=db_name)
        SCHEMA = triplestore.bind("schema", "https://schema.org/")
        triplestore.add_triples(formatted_triples)

    except Exception as err:
        print("Exception occurred in /databases/{}/pgbs/model_evaluation: {}".format(db_name, err))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cannot connect to Stardog instance")

    return TraningEvaluationResponse(model_evaluation_uri = model_evaluation_uri)