"""
Модуль управления прокси
"""
import json
from typing import List, Optional, Dict
from pathlib import Path
from proxy_checker import ProxyResult
from logger import setup_logger
from config import RESULTS_FILE

logger = setup_logger(__name__)


class ProxyManager:
    """Класс управления прокси"""
    
    def __init__(self):
        """Инициализация менеджера"""
        self.proxies: List[ProxyResult] = []
        self.current_proxy: Optional[ProxyResult] = None
    
    def add_results(self, results: List[ProxyResult]):
        """
        Добавляет результаты проверки
        
        Args:
            results: Список результатов
        """
        self.proxies = results
        self._sort_by_speed()
        logger.info(f"Добавлено {len(results)} результатов")
    
    def _sort_by_speed(self):
        """Сортирует прокси по скорости (от быстрейших к медленным)"""
        self.proxies.sort(
            key=lambda x: (not x.is_working, x.response_time)
        )
    
    def get_working_proxies(self) -> List[ProxyResult]:
        """Возвращает только рабочие прокси"""
        return [p for p in self.proxies if p.is_working]
    
    def get_best_proxy(self) -> Optional[ProxyResult]:
        """
        Возвращает лучший прокси (с наименьшим ping)
        
        Returns:
            Лучший рабочий прокси или None
        """
        working = self.get_working_proxies()
        if working:
            self.current_proxy = working[0]
            logger.info(f"Выбран лучший прокси: {self.current_proxy.proxy} "
                       f"(ping: {self.current_proxy.response_time:.2f}ms)")
            return self.current_proxy
        
        logger.warning("Нет рабочих прокси")
        return None
    
    def get_top_proxies(self, count: int = 5) -> List[ProxyResult]:
        """
        Возвращает топ N прокси
        
        Args:
            count: Количество прокси
            
        Returns:
            Список топ прокси
        """
        return self.get_working_proxies()[:count]
    
    def select_proxy_by_index(self, index: int) -> Optional[ProxyResult]:
        """
        Выбирает прокси по индексу
        
        Args:
            index: Индекс прокси
            
        Returns:
            Выбранный прокси или None
        """
        working = self.get_working_proxies()
        
        if 0 <= index < len(working):
            self.current_proxy = working[index]
            logger.info(f"Выбран прокси по индексу {index}: {self.current_proxy.proxy}")
            return self.current_proxy
        
        logger.error(f"Индекс {index} вне диапазона (0-{len(working)-1})")
        return None
    
    def get_current_proxy(self) -> Optional[str]:
        """Возвращает текущий выбранный прокси"""
        if self.current_proxy:
            return self.current_proxy.proxy
        return None
    
    def save_results(self, filepath: Path = RESULTS_FILE):
        """
        Сохраняет результаты в JSON файл
        
        Args:
            filepath: Путь к файлу
        """
        try:
            data = {
                'total': len(self.proxies),
                'working': len(self.get_working_proxies()),
                'results': [p.to_dict() for p in self.proxies]
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Результаты сохранены в {filepath}")
        
        except Exception as e:
            logger.error(f"Ошибка при сохранении результатов: {e}")
    
    def load_from_cache(self, filepath: Path = RESULTS_FILE) -> bool:
        """
        Загружает результаты из кэша
        
        Args:
            filepath: Путь к файлу
            
        Returns:
            True если успешно загружено
        """
        try:
            if not filepath.exists():
                logger.warning(f"Файл кэша {filepath} не найден")
                return False
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.proxies = [
                ProxyResult(
                    proxy=r['proxy'],
                    is_working=r['is_working'],
                    response_time=r['response_time'],
                    timestamp=r['timestamp'],
                    error=r.get('error')
                )
                for r in data.get('results', [])
            ]
            
            self._sort_by_speed()
            logger.info(f"Загружено {len(self.proxies)} прокси из кэша")
            return True
        
        except Exception as e:
            logger.error(f"Ошибка при загрузке кэша: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """
        Возвращает статистику
        
        Returns:
            Словарь со статистикой
        """
        working = self.get_working_proxies()
        
        avg_response = 0
        if working:
            avg_response = sum(p.response_time for p in working) / len(working)
        
        return {
            'total': len(self.proxies),
            'working': len(working),
            'not_working': len(self.proxies) - len(working),
            'success_rate': (len(working) / len(self.proxies) * 100) if self.proxies else 0,
            'avg_response_time': avg_response,
            'best_proxy': working[0].proxy if working else None,
            'best_response_time': working[0].response_time if working else None
        }
    
    def print_proxies(self, proxies: Optional[List[ProxyResult]] = None, max_count: int = 10):
        """
        Красиво выводит прокси в консоль
        
        Args:
            proxies: Список прокси (если None, выводит все рабочие)
            max_count: Максимум для вывода
        """
        if proxies is None:
            proxies = self.get_working_proxies()
        
        if not proxies:
            print("\n⚠️  Нет прокси для отображения\n")
            return
        
        proxies = proxies[:max_count]
        
        print("\n" + "="*80)
        print(f"{'№':<3} {'IP:PORT':<20} {'СТАТУС':<12} {'PING (ms)':<15} {'ОШИБКА':<20}")
        print("="*80)
        
        for i, proxy in enumerate(proxies, 1):
            status = "✓ Работает" if proxy.is_working else "✗ Не работает"
            ping = f"{proxy.response_time:.2f}" if proxy.is_working else "—"
            error = proxy.error if proxy.error else "—"
            
            print(f"{i:<3} {proxy.proxy:<20} {status:<12} {ping:<15} {error:<20}")
        
        print("="*80 + "\n")
