"""
Конфигурация приложения
"""
import os
from pathlib import Path

# Пути
PROJECT_ROOT = Path(__file__).parent
PROXIES_FILE = PROJECT_ROOT / "proxies.txt"
RESULTS_FILE = PROJECT_ROOT / "results.json"
LOG_FILE = PROJECT_ROOT / "proxy_manager.log"

# Параметры проверки прокси
CHECK_TIMEOUT = 5  # Таймаут в секундах
MAX_CONCURRENT = 10  # Максимум одновременных запросов
TEST_URL = "http://httpbin.org/ip"  # URL для проверки
TEST_HTTPS_URL = "https://httpbin.org/ip"  # HTTPS URL

# Параметры логирования
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# API для загрузки прокси
FREE_PROXY_API = "https://www.proxy-list.download/api/v1/get?type=http"
