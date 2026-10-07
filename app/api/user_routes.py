"""REST API routes for User management coordinating with ApiUserController."""

from fastapi import APIRouter, Path as PathParam, Response, status
from app.controllers.api_user_controller import ApiUserController
from app.schemas.user_schemas import (
    UserCreateRequest,
    UserUpdateRequest,
    UserPatchRequest,
    UserApiResponse,
    UserListApiResponse,
    UserDeleteApiResponse,
)

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get(
    "",
    response_model=UserListApiResponse,
    summary="List All Users",
    description="Retrieves a list of all alumni/users stored in memory via ApiUserController.",
)
@router.get(
    "/",
    response_model=UserListApiResponse,
    include_in_schema=False,
)
async def list_users():
    """Retrieves all users via ApiUserController."""
    return ApiUserController.get_users()


@router.post(
    "",
    response_model=UserApiResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create User",
    description="Creates a new alumni/user in memory via ApiUserController.",
)
@router.post(
    "/",
    response_model=UserApiResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
async def create_user(payload: UserCreateRequest):
    """Creates a new user via ApiUserController."""
    return ApiUserController.create_user(payload.model_dump())


@router.get(
    "/{id}",
    response_model=UserApiResponse,
    summary="Get User by ID",
    description="Retrieves a specific alumni/user by their unique numeric ID via ApiUserController.",
)
async def get_user(
    response: Response,
    id: int = PathParam(..., description="Unique integer ID of the user", examples=[1]),
):
    """Retrieves a user by ID via ApiUserController."""
    result = ApiUserController.get_user(id)
    if result.get("status") == "error":
        response.status_code = status.HTTP_404_NOT_FOUND
    return result


@router.put(
    "/{id}",
    response_model=UserApiResponse,
    summary="Full Update User",
    description="Completely updates all fields of an existing user via ApiUserController.",
)
async def update_user(
    payload: UserUpdateRequest,
    response: Response,
    id: int = PathParam(..., description="Unique integer ID of the user to update", examples=[1]),
):
    """Fully updates a user via ApiUserController."""
    result = ApiUserController.update_user(id, user_or_data=payload.model_dump())
    if result.get("status") == "error":
        response.status_code = status.HTTP_404_NOT_FOUND
    return result


@router.patch(
    "/{id}",
    response_model=UserApiResponse,
    summary="Partial Update User",
    description="Partially updates specified fields of an existing user via ApiUserController.",
)
async def patch_user(
    payload: UserPatchRequest,
    response: Response,
    id: int = PathParam(..., description="Unique integer ID of the user to patch", examples=[1]),
):
    """Partially updates a user via ApiUserController."""
    result = ApiUserController.update_user(id, user_or_data=payload.model_dump(exclude_unset=True))
    if result.get("status") == "error":
        response.status_code = status.HTTP_404_NOT_FOUND
    return result


@router.delete(
    "/{id}",
    response_model=UserDeleteApiResponse,
    summary="Delete User",
    description="Deletes an existing user from in-memory storage via ApiUserController.",
)
async def delete_user(
    response: Response,
    id: int = PathParam(..., description="Unique integer ID of the user to delete", examples=[1]),
):
    """Deletes a user via ApiUserController."""
    result = ApiUserController.delete_user(id)
    if result.get("status") == "error":
        response.status_code = status.HTTP_404_NOT_FOUND
    return result
