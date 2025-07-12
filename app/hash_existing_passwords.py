from database import SessionLocal
from models import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_passwords():
    db = SessionLocal()
    users = db.query(User).all()
    for user in users:
        if not user.password.startswith("$2b$"):  # значит пароль не хеширован
            user.password = pwd_context.hash(user.password)
            print(f"Хешируем пароль для пользователя: {user.username}")
    db.commit()
    db.close()

if __name__ == "__main__":
    hash_passwords()
