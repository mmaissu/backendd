from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.note import NoteCreate, NoteUpdate, NoteOut
from crud import create_note, get_notes, get_note, update_note, delete_note
from dependencies import get_current_user, get_db
from models import User
from redis_client import get_cache_manager
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notes", tags=["notes"])

@router.post("/", response_model=NoteOut)
async def create(
    user_note: NoteCreate, 
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user),
    cache_manager = Depends(get_cache_manager)
):
    """Создание новой заметки с инвалидацией кеша"""
    note = await create_note(user_note, current_user.id, db)
    
    # Инвалидируем кеш для заметок пользователя
    await cache_manager.delete_pattern(f"user_notes:{current_user.id}:*")
    await cache_manager.delete_pattern("notes:all:*")
    
    logger.info(f"📝 Created note {note.id} for user {current_user.id}")
    return note

from typing import Optional
from fastapi import Query

@router.get("/", response_model=list[NoteOut])
async def read_notes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, le=100),
    search: Optional[str] = "",
    cache_manager = Depends(get_cache_manager)
):
    """Получение списка заметок с кешированием"""
    # Генерируем ключ кеша
    cache_key = f"user_notes:{current_user.id}:{skip}:{limit}:{search}"
    
    # Проверяем кеш
    cached_notes = await cache_manager.get(cache_key)
    if cached_notes:
        logger.info(f"📦 Returning cached notes for user {current_user.id}")
        return cached_notes
    
    # Получаем данные из БД
    notes = await get_notes(current_user.id, db, skip=skip, limit=limit, search=search)
    
    # Сериализуем для кеширования
    notes_data = [note.model_dump() for note in notes]
    
    # Кешируем результат (TTL: 5 минут)
    await cache_manager.set(cache_key, notes_data, ttl=300)
    
    logger.info(f"💾 Cached notes for user {current_user.id}")
    return notes_data

@router.get("/{note_id}", response_model=NoteOut)
async def read_note(
    note_id: int, 
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user),
    cache_manager = Depends(get_cache_manager)
):
    """Получение конкретной заметки с кешированием"""
    # Генерируем ключ кеша
    cache_key = f"note:{note_id}:user:{current_user.id}"
    
    # Проверяем кеш
    cached_note = await cache_manager.get(cache_key)
    if cached_note:
        logger.info(f"📦 Returning cached note {note_id} for user {current_user.id}")
        return cached_note
    
    # Получаем из БД
    note = await get_note(note_id, current_user.id, db)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Кешируем результат
    note_data = note.model_dump()
    await cache_manager.set(cache_key, note_data, ttl=600)  # 10 минут для отдельных заметок
    
    logger.info(f"💾 Cached note {note_id} for user {current_user.id}")
    return note_data

@router.put("/{note_id}", response_model=NoteOut)
async def update(
    note_id: int, 
    updated: NoteUpdate, 
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user),
    cache_manager = Depends(get_cache_manager)
):
    """Обновление заметки с инвалидацией кеша"""
    note = await update_note(note_id, current_user.id, updated, db)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Инвалидируем кеш
    await cache_manager.delete(f"note:{note_id}:user:{current_user.id}")
    await cache_manager.delete_pattern(f"user_notes:{current_user.id}:*")
    
    logger.info(f"✏️ Updated note {note_id} for user {current_user.id}")
    return note

@router.delete("/{note_id}")
async def delete(
    note_id: int, 
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user),
    cache_manager = Depends(get_cache_manager)
):
    """Удаление заметки с инвалидацией кеша"""
    note = await delete_note(note_id, current_user.id, db)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Инвалидируем кеш
    await cache_manager.delete(f"note:{note_id}:user:{current_user.id}")
    await cache_manager.delete_pattern(f"user_notes:{current_user.id}:*")
    
    logger.info(f"🗑️ Deleted note {note_id} for user {current_user.id}")
    return {"message": "Note deleted"}
