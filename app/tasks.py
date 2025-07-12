import time
import logging
from celery_app import celery_app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def send_email_task(self, email: str, subject: str, message: str):
    """
    Имитация отправки email - длительная задача
    """
    logger.info(f"Начинаю отправку email на {email}")
    

    for i in range(10):
        time.sleep(1)  # Имитация работы
        logger.info(f"Обработка email {i+1}/10")
        
        
        self.update_state(
            state="PROGRESS",
            meta={"current": i + 1, "total": 10, "status": f"Обработка {i+1}/10"}
        )
    
    
    time.sleep(2)
    logger.info(f"Email успешно отправлен на {email}")
    
    return {
        "status": "success",
        "email": email,
        "subject": subject,
        "message": message,
        "result": "Email отправлен успешно"
    }

@celery_app.task
def process_data_task(data: dict):
    """
    Пример другой длительной задачи для обработки данных
    """
    logger.info(f"Начинаю обработку данных: {data}")
    
   
    time.sleep(5)
    
    
    processed_data = {
        "original": data,
        "processed": True,
        "timestamp": time.time(),
        "items_count": len(data) if isinstance(data, dict) else 0
    }
    
    logger.info(f"Данные обработаны: {processed_data}")
    return processed_data

@celery_app.task
def cleanup_task():
    """
    Задача для очистки временных данных
    """
    logger.info("Начинаю очистку временных данных")
    
    
    time.sleep(3)
    
    logger.info("Очистка завершена")
    return {"status": "cleaned", "message": "Временные данные очищены"} 