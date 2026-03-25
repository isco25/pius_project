from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.security import TokenError, decode_access_token
from app.users.schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.users.service import UserService


router = APIRouter()
bearer_scheme = HTTPBearer(auto_error=False)


def get_user_service(request: Request) -> UserService:
    return UserService(
        repository=request.app.state.user_repository,
        settings=request.app.state.settings,
    )


def require_authentication(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> int:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    try:
        payload = decode_access_token(
            token=credentials.credentials,
            secret=request.app.state.settings.jwt_secret,
            algorithm=request.app.state.settings.jwt_algorithm,
        )
    except TokenError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from error

    try:
        return int(payload["sub"])
    except (KeyError, TypeError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject",
        ) from error


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    payload: RegisterRequest,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    try:
        user = service.register_user(payload.email, payload.password)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    return UserResponse.from_model(user)


@router.post("/login", response_model=TokenResponse)
def login_user(
    payload: LoginRequest,
    service: UserService = Depends(get_user_service),
) -> TokenResponse:
    try:
        access_token = service.login_user(payload.email, payload.password)
    except PermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        ) from error
    return TokenResponse(access_token=access_token)


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
    _: int = Depends(require_authentication),
) -> UserResponse:
    try:
        user = service.get_user(user_id)
    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    return UserResponse.from_model(user)

