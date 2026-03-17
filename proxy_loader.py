"""
Модуль для загрузки прокси из различных источников
"""
import json
import asyncio
from typing import List, Set
from pathlib import Path
import aiohttp
import requests
from logger import setup_logger
from config import PROXIES_FILE, FREE_PROXY_API

logger = setup_logger(__name__)


class ProxyLoader:
    """Класс для загрузки прокси из файлов и API"""
    
    def __init__(self):
        self.proxies: Set[str] = set()
    
    def load_from_file(self, filepath: Path = PROXIES_FILE) -> List[str]:
        """
        Загружает прокси из текстового файла
        
        Формат: ip:port
        
        Args:
            filepath: Путь к файлу
            
        Returns:
            Список прокси
        """
        proxies = []
        
        try:
            if not filepath.exists():
                logger.warning(f"Файл {filepath} не найден")
                return proxies
            
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):  # Пропускаем комментарии
                        if self._is_valid_proxy(line):
                            proxies.append(line)
                            self.proxies.add(line)
            
            logger.info(f"Загружено {len(proxies)} прокси из файла {filepath}")
            return proxies
        
        except Exception as e:
            logger.error(f"Ошибка при загрузке файла: {e}")
            return proxies
    
    async def load_from_api(self) -> List[str]:
        """
        Загружает прокси из API
        
        Returns:
            Список прокси
        """
        proxies = []
        
        try:
            # Используем requests для простоты
            response = requests.get(FREE_PROXY_API, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'RESULT' in data:
                for proxy_data in data['RESULT']:
                    proxy = f"{proxy_data['IP']}:{proxy_data['PORT']}"
                    if self._is_valid_proxy(proxy):
                        proxies.append(proxy)
                        self.proxies.add(proxy)
            
            logger.info(f"Загружено {len(proxies)} прокси из API")
            return proxies
        
        except requests.RequestException as e:
            logger.error(f"Ошибка при загрузке из API: {e}")
            return proxies
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON: {e}")
            return proxies
        except Exception as e:
            logger.error(f"Неизвестная ошибка при загрузке из API: {e}")
            return proxies
    
    @staticmethod
    def _is_valid_proxy(proxy: str) -> bool:
        """
        Проверяет формат прокси (ip:port)
        
        Args:
            proxy: Строка прокси
            
        Returns:
            True если формат корректен
        """
        try:
            parts = proxy.split(':')
            if len(parts) != 2:
                return False
            
            ip, port = parts
            
            # Проверка IP
            octets = ip.split('.')
            if len(octets) != 4:
                return False
            
            for octet in octets:
                num = int(octet)
                if not (0 <= num <= 255):
                    return False
            
            # Проверка портa
            port_num = int(port)
            if not (1 <= port_num <= 65535):
                return False
            
            return True
        except (ValueError, AttributeError):
            return False
    
    def get_all_proxies(self) -> List[str]:
        """Возвращает все загруженные прокси"""
        return list(self.proxies)
    
    def clear(self):
        """Очищает список прокси"""
        self.proxies.clear()
        logger.info("Список прокси очищен")
