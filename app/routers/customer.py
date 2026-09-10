from fastapi import APIRouter, Depends

from app.dependencies import require_role
from app.models.user import User

router = APIRouter(
    prefix="/customer",
    tags=["Customer"]
)

@router.get("/protected")
def customer_protected(
    current_user : User = Depends(require_role("CUSTOMER"))
):
    return {
        "message": "Customer authorization successful",
        "user_id": current_user.id,
        "name": current_user.name,
        "role": current_user.role
    }