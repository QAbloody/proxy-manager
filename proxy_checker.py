"""
Модуль для проверки работоспособности прокси
"""
import asyncio
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import aiohttp
from logger import setup_logger
from config import CHECK_TIMEOUT, MAX_CONCURRENT, TEST_URL

logger = setup_logger(__name__)


@dataclass
class ProxyResult:
    """Результат проверки прокси"""
    proxy: str
    is_working: bool
    response_time: float  # в миллисекундах
    timestamp: float
    error: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Преобразует результат в словарь"""
        return asdict(self)


class ProxyChecker:
    """Класс для проверки прокси"""
    
    def __init__(self, timeout: int = CHECK_TIMEOUT, max_concurrent: int = MAX_CONCURRENT):
        """
        Инициализация
        
        Args:
            timeout: Таймаут проверки в секундах
            max_concurrent: Максимум одновременных запросов
        """
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def check_proxy(self, proxy: str, url: str = TEST_URL) -> ProxyResult:
        """
        Проверяет отдельный прокси
        
        Args:
            proxy: Строка прокси (ip:port)
            url: URL для проверки
            
        Returns:
            Результат проверки
        """
        async with self.semaphore:
            start_time = time.time()
            proxy_url = f"http://{proxy}"
            
            try:
                # Создаём session с прокси
                connector = aiohttp.TCPConnector(ssl=False)
                async with aiohttp.ClientSession(
                    connector=connector,
                    timeout=self.timeout
                ) as session:
                    async with session.get(
                        url,
                        proxy=proxy_url,
                        allow_redirects=True
                    ) as response:
                        response_time = (time.time() - start_time) * 1000  # В миллисекундах
                        
                        if response.status == 200:
                            logger.debug(f"✓ Прокси {proxy} рабочий (ping: {response_time:.2f}ms)")
                            return ProxyResult(
                                proxy=proxy,
                                is_working=True,
                                response_time=response_time,
                                timestamp=time.time()
                            )
                        else:
                            error = f"Status code: {response.status}"
                            logger.debug(f"✗ Прокси {proxy} вернул статус {response.status}")
                            return ProxyResult(
                                proxy=proxy,
                                is_working=False,
                                response_time=response_time,
                                timestamp=time.time(),
                                error=error
                            )
            
            except asyncio.TimeoutError:
                response_time = (time.time() - start_time) * 1000
                error = "Timeout"
                logger.debug(f"✗ Прокси {proxy} timeout")
                return ProxyResult(
                    proxy=proxy,
                    is_working=False,
                    response_time=response_time,
                    timestamp=time.time(),
                    error=error
                )
            
            except aiohttp.ClientError as e:
                response_time = (time.time() - start_time) * 1000
                error = str(e)
                logger.debug(f"✗ Прокси {proxy} ошибка: {error}")
                return ProxyResult(
                    proxy=proxy,
                    is_working=False,
                    response_time=response_time,
                    timestamp=time.time(),
                    error=error
                )
            
            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                error = f"Unexpected error: {str(e)}"
                logger.error(f"✗ Прокси {proxy} неожиданная ошибка: {error}")
                return ProxyResult(
                    proxy=proxy,
                    is_working=False,
                    response_time=response_time,
                    timestamp=time.time(),
                    error=error
                )
    
    async def check_multiple(self, proxies: List[str], url: str = TEST_URL) -> List[ProxyResult]:
        """
        Проверяет несколько прокси параллельно
        
        Args:
            proxies: Список прокси
            url: URL для проверки
            
        Returns:
            Список результатов
        """
        logger.info(f"Начинаю проверку {len(proxies)} прокси...")
        
        tasks = [self.check_proxy(proxy, url) for proxy in proxies]
        results = await asyncio.gather(*tasks)
        
        working = sum(1 for r in results if r.is_working)
        logger.info(f"Проверка завершена. Рабочих прокси: {working}/{len(proxies)}")
        
        return results
