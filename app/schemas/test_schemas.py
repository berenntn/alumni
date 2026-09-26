"""Pydantic schemas for initial test endpoints."""

from typing import Union
from pydantic import BaseModel, Field


class HelloResponse(BaseModel):
    """Response schema for greeting endpoints."""
    message: str = Field(..., description="Greeting message", examples=["Hello, World!"])


class SumResponse(BaseModel):
    """Response schema for mathematical sum endpoint."""
    number1: Union[int, float] = Field(..., description="First input number", examples=[10])
    number2: Union[int, float] = Field(..., description="Second input number", examples=[25])
    operation: str = Field(default="sum", description="Applied mathematical operation")
    result: Union[int, float] = Field(..., description="Calculated sum of the two numbers", examples=[35])
