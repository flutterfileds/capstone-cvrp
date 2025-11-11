from fastapi import FastAPI, HTTPException
"""from fastapi.middleware.cors import CORSMiddleware
from contextlib import contextmanager"""
import time
from datetime import datetime

from app.models import CVRPRequest, CVRPSolution
from app.services.ga_solver import GASolver
from app.services.nn_solver import NNSolver

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Welcome to  CVRP Solver API!"}\
    
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/solve-ga", response_model=CVRPSolution)
def solve_ga(request: CVRPRequest):
    
    bins_data = [{"id": "depot", "demand": 0}]
    bins_data.extend([{"id": b.id, "demand": b.demand} for b in request.bins])
    
    solver = GASolver(
        bins=bins_data,
        distance_matrix=request.distance_matrix
    )
    result = solver.solve()
    
    response = CVRPSolution(
        success=True,
        created_at=datetime.now(),
        number_of_trucks=result['number_of_trucks'],
        total_distance=result["total_distance"],
        total_emissions=result["total_emissions"],
        avg_utilization=result["avg_utilization"],
        best_fitness=result["best_fitness"],
        generations_run=result["generations_run"],
        computation_time=result['computation_time'],
        routes=result["route_details"]
    )

    return response

@app.post("/solve-nn", response_model=CVRPSolution)
def solve_nn(request: CVRPRequest):

    bins_data = [{"id": "depot", "demand": 0}]
    bins_data.extend([{"id": b.id, "demand": b.demand} for b in request.bins])

    solver = NNSolver(bins_data, request.distance_matrix)
    result = solver.solve()

    response = CVRPSolution(
        success=True,
        created_at=datetime.now(),
        number_of_trucks=result['number_of_trucks'],
        total_distance=result["total_distance"],
        total_emissions=result["total_emissions"],
        avg_utilization=result["avg_utilization"],
        best_fitness=result["best_fitness"],
        generations_run=result["generations_run"],
        computation_time=result['computation_time'],
        routes=result["route_details"]
    )

    return response
