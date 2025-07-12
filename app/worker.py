#!/usr/bin/env python3
"""
Celery Worker для обработки фоновых задач
"""
import os
import sys

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from celery_app import celery_app

if __name__ == "__main__":
    celery_app.start() 