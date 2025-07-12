from models import Note
from schemas.note import NoteCreate, NoteUpdate, NoteOut
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import User

async def create_note(note_data: NoteCreate, user_id: int, db: AsyncSession):
    new_note = Note(
        text=note_data.text,
        owner_id=user_id
    )
    db.add(new_note)
    await db.commit()
    await db.refresh(new_note)
    return new_note


async def get_all_notes(session: AsyncSession):
    result = await session.execute(select(Note))
    notes = result.scalars().all()
    return notes

from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from schemas.user import UserCreate, UserLogin, UserOut, TokenData
from models import User
from sqlalchemy.ext.asyncio import AsyncSession
from auth import get_password_hash

async def create_user(user: UserCreate, session: AsyncSession):
    hashed_password = get_password_hash(user.password)
    new_user = User(username=user.username, password=hashed_password, role='user')
    session.add(new_user)
    try:
        await session.commit()
        await session.refresh(new_user)
        return new_user
    except IntegrityError:
        await session.rollback()
        return None

async def get_user_by_username(username: str, session: AsyncSession):
    result = await session.execute(select(User).where(User.username == username))
    return result.scalars().first()


from auth import verify_password  # импортируй, если не импортировал

async def authenticate_user(user: UserLogin, session: AsyncSession):
    result = await session.execute(select(User).where(User.username == user.username))
    db_user = result.scalars().first()
    if db_user and verify_password(user.password, db_user.password):
        return db_user
    return None

async def get_all_users(session: AsyncSession):
    result = await session.execute(select(User))
    users = result.scalars().all()
    return users

async def create_note(note_data, user_id: int, db: AsyncSession):
    new_note = Note(
        text=note_data.text,
        owner_id=user_id
    )
    db.add(new_note)
    await db.commit()
    await db.refresh(new_note)
    return new_note

from sqlalchemy import select
from sqlalchemy import or_

async def get_notes(
    user_id: int,
    db: AsyncSession,
    skip: int = 0,
    limit: int = 10,
    search: str = ""
):
    query = select(Note).where(Note.owner_id == user_id)

    if search:
        query = query.where(Note.text.ilike(f"%{search}%"))

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


async def get_note(note_id: int, user_id: int, db: AsyncSession):
    result = await db.execute(select(Note).where(Note.id == note_id, Note.owner_id == user_id))
    return result.scalar_one_or_none()

async def update_note(note_id: int, user_id: int, data, db: AsyncSession):
    note = await get_note(note_id, user_id, db)
    if note:
        for key, value in data.dict(exclude_unset=True).items():
            setattr(note, key, value)
        await db.commit()
        await db.refresh(note)
    return note

async def delete_note(note_id: int, user_id: int, db: AsyncSession):
    note = await get_note(note_id, user_id, db)
    if note:
        await db.delete(note)
        await db.commit()
    return note