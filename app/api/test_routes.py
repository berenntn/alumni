"""Initial test endpoints demonstrating layered architecture and Pydantic validation."""

from typing import Union
from fastapi import APIRouter, Path as PathParam
from app.schemas.test_schemas import HelloResponse, SumResponse
from app.services.calculator_service import CalculatorService

test_router = APIRouter(tags=["Test Endpoints"])


@test_router.get(
    "/hello",
    response_model=HelloResponse,
    summary="General Greeting",
    description="Returns a default Hello World JSON message.",
)
async def get_hello() -> HelloResponse:
    """Returns the default greeting message."""
    return HelloResponse(message="Hello, World!")


@test_router.get(
    "/hello/{name}",
    response_model=HelloResponse,
    summary="Personalized Greeting",
    description="Returns a personalized greeting message for the specified name.",
)
async def get_hello_name(
    name: str = PathParam(..., description="The name of the person to greet", examples=["Berkay"])
) -> HelloResponse:
    """Returns a personalized greeting message."""
    return HelloResponse(message=f"Hello, {name}!")


@test_router.get(
    "/sum/{a}/{b}",
    response_model=SumResponse,
    summary="Sum Calculation",
    description="Calculates and returns the sum of two numbers using the service layer.",
)
async def get_sum(
    number1: float = PathParam(..., description="The first number", examples=[15]),
    number2: float = PathParam(..., description="The second number", examples=[27]),
) -> SumResponse:
    """Calculates the sum of two numbers and returns the structured result."""
    # Convert whole numbers to int for cleaner output presentation
    n1 = int(a) if a.is_integer() else a
    n2 = int(b) if b.is_integer() else b

    calculated_result = CalculatorService.add(n1, n2)

    return SumResponse(
        number1=n1,
        number2=n2,
        operation="sum",
        result=calculated_result,
    )
