from typing import List, Optional
from pydantic import BaseModel, Field, field_validator 
from datetime import datetime

class Bin(BaseModel):
    id: str
    demand: float = Field(..., ge=0)

class Depot(BaseModel):
    id: str = "depot"

class CVRPRequest(BaseModel):
    bins: List[Bin]
    distance_matrix: List[List[float]]

    @field_validator('bins')
    @classmethod
    def validate_unique_ids(cls, bins):
        ids = [b.id for b in bins]
        if len(ids) != len(set(ids)):
            raise ValueError("Bin IDs must be unique")
        return bins
    
class RouteDetail(BaseModel):
    truck_no: int
    route: List[str]
    distance: float
    load: float
    utilization: float
    unused_capacity: float
    emissions: float

class CVRPSolution(BaseModel):
    """Response model for CVRP optimization"""
    success: bool
    created_at: datetime
    routes: List[RouteDetail]
    number_of_trucks: int
    total_distance: float
    total_emissions: float
    avg_utilization: float
    best_fitness: float
    generations_run: int
    computation_time: float