from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.note import NoteCreate, NoteOut
from database import get_db
from redis_client import get_cache_manager
from config import settings
import crud
import json

app = FastAPI(title=settings.PROJECT_NAME, version="1.0.0")

@app.post("/notes", response_model=NoteOut)
async def create_note(
    note: NoteCreate,
    session: AsyncSession = Depends(get_db),
    cache_manager = Depends(get_cache_manager)
):
    created_note = await crud.create_note(note, user_id=1, db=session)  # user_id=1 для примера
    # Инвалидация кеша
    await cache_manager.delete_pattern("notes:all*")
    return created_note

@app.get("/notes", response_model=list[NoteOut])
async def read_notes(
    session: AsyncSession = Depends(get_db),
    cache_manager = Depends(get_cache_manager)
):
    cache_key = "notes:all"
    cached = await cache_manager.get(cache_key)
    if cached:
        return cached
    notes = await crud.get_all_notes(session)
    serialized = [note.model_dump() for note in notes]
    await cache_manager.set(cache_key, serialized, ttl=300)
    return serialized
