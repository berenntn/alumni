from fastapi import APIRouter
from app.controllers.api_user_controller import ApiUserController
from app.models.user import User

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("", summary="List all users via ApiUserController")
@router.get("/", summary="List all users via ApiUserController", include_in_schema=False)
async def list_users():
    """Retrieves all users via ApiUserController."""
    return ApiUserController.get_users()


@router.post("", status_code=201, summary="Create user via ApiUserController")
@router.post("/", status_code=201, summary="Create user via ApiUserController", include_in_schema=False)
async def create_user_endpoint(user: User):
    """Creates a new user via ApiUserController."""
    return ApiUserController.create_user(user)


@router.get("/{id}")
async def get_user(id: int):
    return {"id": id, "method": "GET", "status": "ok"}


@router.put("/{id}")
async def update_user(id: int):
    return {"id": id, "method": "PUT", "status": "updated"}


@router.patch("/{id}")
async def patch_user(id: int):
    return {"id": id, "method": "PATCH", "status": "updated"}


@router.delete("/{id}")
async def delete_user(id: int):
    return {"id": id, "method": "DELETE", "status": "deleted"}
