from fastapi import APIRouter, Depends ,HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    RegisterRequest,
    AuthResponse,
    LoginRequest,
    )
from app.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
)
from app.dependencies import get_current_user

router = APIRouter(
    prefix = "/auth",
    tags = ["Authentication"]
)

@router.post("/register",response_model = AuthResponse)
def register(
    data: RegisterRequest,
    db : Session = Depends(get_db)
):
    # Check email
    existing_email = (
        db.query(User).filter(
            User.email == data.email
        ).first()
    )

    if existing_email:
        raise HTTPException(
            status_code = 400,
            detail= " Email already registered"
        )

    #check phone
    existing_phone = (
        db.query(User).filter(
            User.phone == data .phone
        ).first()
    )

    if existing_phone:
        raise HTTPException(
            status_code = 400,
            detail ="phone number already registered"
        )

    #create user
    user = User(
        name = data.name,
        email = data.email, 
        phone = data. phone ,
        password_hash = hash_password(data.password),
        role = data.role,
        is_active = True
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    #create jwt token
    access_token = create_access_token({
        "sub" : str(user.id),
        "role": user.role
    })

    return{
        "message": "Registration successful",
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role
    }


@router.post("/login",response_model = AuthResponse)
def login(
    data : LoginRequest,
    db : Session = Depends(get_db)
):
    user= (
        db.query(User).filter(
            User.email == data.email
        ).first()
    )

    if not user :
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="User account is inactive"
        )

    if not verify_password(
        data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    access_token = create_access_token({
        "sub": str(user.id),
        "role": user.role
    })

    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role
    }

@router.get("/me")
def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    return {
        "message": "JWT authorization successful",
        "user_id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "phone": current_user.phone,
        "role": current_user.role
    }