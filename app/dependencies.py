from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models import User
from auth import SECRET_KEY, ALGORITHM
from crud import get_user_by_username
from schemas.user import TokenData
import jwt_utils
from typing import AsyncGenerator

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

async def get_current_user(token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, jwt_utils.SECRET_KEY, algorithms=[jwt_utils.ALGORITHM])
        username: str = payload.get("sub")
        token_data = TokenData(username=username)
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await get_user_by_username(username, session)
    if user is None:
        raise credentials_exception
    return user

def require_role(required_role: str):
    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission"
            )
        return current_user
    return role_checker

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session