"""
Модуль логирования
"""
import logging
import sys
from config import LOG_FILE, LOG_LEVEL, LOG_FORMAT

def setup_logger(name: str) -> logging.Logger:
    """
    Настраивает логгер с выводом в файл и консоль
    
    Args:
        name: Имя логгера
        
    Returns:
        Настроенный логгер
    """
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)
    
    # Форматер
    formatter = logging.Formatter(LOG_FORMAT)
    
    # Обработчик для файла
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(LOG_LEVEL)
    file_handler.setFormatter(formatter)
    
    # Обработчик для консоли
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(LOG_LEVEL)
    console_handler.setFormatter(formatter)
    
    # Добавляем обработчики
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
