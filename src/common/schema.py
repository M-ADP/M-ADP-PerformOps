from typing import Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    message: str
    data: T


class ErrorResponse(BaseModel):
    message: str

class CursorPage(BaseModel, Generic[T]):
    items: list[T]
    has_next: bool

class CursorRequest(BaseModel):
    cursor: int = Query(None)
    size: int = Query(10)
