from pydantic import BaseModel, ConfigDict
from typing import Optional

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class PredictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str

class PredictResponse(BaseModel):
    intent: str
    confidence: float
    message: str

class PredictionRead(BaseModel):
    id: int
    text: str
    intent: str
    confidence: float
    created_at: str

class HealthResponse(BaseModel):
    status: str
    version: str
