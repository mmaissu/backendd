from fastapi import APIRouter
from sqlalchemy.orm import Session
from database import get_db
from schemas.user import UserCreate, UserOut
from models import User
from utils import hash_password
from auth import create_access_token
from fastapi import Depends

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/users/ping")
async def ping():
    return {"message": "pong"}

@router.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_pw = hash_password(user.password)
    db_user = User(username=user.username, password=hashed_pw)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user