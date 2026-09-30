from fastapi import APIRouter

router = APIRouter(prefix="/api/users", tags=["Users"])


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
