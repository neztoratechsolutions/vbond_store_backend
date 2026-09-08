from fastapi import APIRouter, Depends

from app.dependencies import require_role
from app.models.user import User

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)

@router.get("/protected")
def admin_protected(
    current_user: User = Depends(require_role("ADMIN"))
):
    return {
        "message": "Admin authorization successful",
        "user_id": current_user.id,
        "name": current_user.name,
        "role": current_user.role
    }