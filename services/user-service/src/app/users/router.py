from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.security import TokenError, decode_access_token
from app.users.schemas import (
    AnswerCreatedEvent,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
    UserStatsResponse,
)
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


def require_internal_api_key(request: Request) -> None:
    provided_token = request.headers.get("X-Internal-Token")
    authorization_header = request.headers.get("Authorization")

    if provided_token is None and authorization_header is not None:
        scheme, _, token = authorization_header.partition(" ")
        if scheme.lower() == "bearer" and token:
            provided_token = token

    if provided_token != request.app.state.settings.internal_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal API key",
        )


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


@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    responses={status.HTTP_404_NOT_FOUND: {"description": "User not found"}},
)
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


@router.get(
    "/users/{user_id}/stats",
    response_model=UserStatsResponse,
    responses={status.HTTP_404_NOT_FOUND: {"description": "User not found"}},
)
def get_user_stats(
    user_id: int,
    service: UserService = Depends(get_user_service),
) -> UserStatsResponse:
    try:
        user = service.get_user(user_id)
    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    return UserStatsResponse.from_model(user)


@router.get("/leaderboard", response_model=list[UserStatsResponse])
def get_leaderboard(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: UserService = Depends(get_user_service),
) -> list[UserStatsResponse]:
    users = service.get_leaderboard(limit=limit, offset=offset)
    return [UserStatsResponse.from_model(user) for user in users]


@router.post(
    "/internal/events/answer-created",
    response_model=UserStatsResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Invalid internal API key"},
        status.HTTP_404_NOT_FOUND: {"description": "User not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Event processing failed"},
    },
)
def handle_answer_created_event(
    payload: AnswerCreatedEvent,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    service: UserService = Depends(get_user_service),
    _: None = Depends(require_internal_api_key),
) -> UserStatsResponse:
    try:
        result = service.add_xp(
            user_id=payload.user_id,
            answer_id=payload.answer_id,
            idempotency_key=idempotency_key,
        )
    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error
    return UserStatsResponse.from_model(result.user)
