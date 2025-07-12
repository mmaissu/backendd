from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any
from tasks import send_email_task, process_data_task, cleanup_task
from celery.result import AsyncResult
from dependencies import get_current_user
from models import User

router = APIRouter(prefix="/tasks", tags=["tasks"])

class EmailRequest(BaseModel):
    email: str
    subject: str
    message: str

class DataProcessRequest(BaseModel):
    data: Dict[str, Any]

class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str

@router.post("/send-email", response_model=TaskResponse)
async def send_email(
    email_request: EmailRequest
    # current_user: User = Depends(get_current_user)  # Временно отключено для тестирования
):
    """
    Запуск фоновой задачи отправки email
    """
    try:
        # Запускаем задачу асинхронно
        task = send_email_task.delay(
            email_request.email,
            email_request.subject,
            email_request.message
        )
        
        return TaskResponse(
            task_id=task.id,
            status="PENDING",
            message="Задача отправки email запущена"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка запуска задачи: {str(e)}")

@router.post("/process-data", response_model=TaskResponse)
async def process_data(
    data_request: DataProcessRequest
    # current_user: User = Depends(get_current_user)  # Временно отключено для тестирования
):
    """
    Запуск фоновой задачи обработки данных
    """
    try:
        task = process_data_task.delay(data_request.data)
        
        return TaskResponse(
            task_id=task.id,
            status="PENDING",
            message="Задача обработки данных запущена"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка запуска задачи: {str(e)}")

@router.post("/cleanup", response_model=TaskResponse)
async def cleanup(
    # current_user: User = Depends(get_current_user)  # Временно отключено для тестирования
):
    """
    Запуск задачи очистки
    """
    try:
        task = cleanup_task.delay()
        
        return TaskResponse(
            task_id=task.id,
            status="PENDING",
            message="Задача очистки запущена"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка запуска задачи: {str(e)}")

@router.get("/status/{task_id}")
async def get_task_status(task_id: str
    # current_user: User = Depends(get_current_user)  # Временно отключено для тестирования
):
    """
    Получение статуса задачи по ID
    """
    try:
        task_result = AsyncResult(task_id)
        
        response = {
            "task_id": task_id,
            "status": task_result.status,
        }
        
        if task_result.ready():
            if task_result.successful():
                response["result"] = task_result.result
            else:
                response["error"] = str(task_result.info)
        elif task_result.state == "PROGRESS":
            response["progress"] = task_result.info
            
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения статуса: {str(e)}")

@router.get("/tasks")
async def list_tasks(
    # current_user: User = Depends(get_current_user)  # Временно отключено для тестирования
):
    """
    Получение списка активных задач (упрощенная версия)
    """
    # В реальном приложении здесь можно добавить логику для получения списка задач
    return {
        "message": "Список задач",
        "note": "Для получения списка всех задач используйте Celery inspect"
    } 