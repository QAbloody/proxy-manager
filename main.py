"""
Главный модуль с CLI интерфейсом
"""
import asyncio
import sys
from pathlib import Path
from typing import Optional
from colorama import Fore, Style, init

from logger import setup_logger
from proxy_loader import ProxyLoader
from proxy_checker import ProxyChecker
from proxy_manager import ProxyManager
from config import PROXIES_FILE

# Инициализируем colorama для цветного вывода
init(autoreset=True)

logger = setup_logger(__name__)

# Глобальные объекты
loader = ProxyLoader()
checker = ProxyChecker()
manager = ProxyManager()


def print_header():
    """Выводит заголовок программы"""
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.CYAN}{'PROXY MANAGER - Менеджер прокси v1.0':^80}")
    print(f"{Fore.CYAN}{'='*80}\n")


def print_menu():
    """Выводит главное меню"""
    print(f"\n{Fore.YELLOW}{'ГЛАВНОЕ МЕНЮ':^80}")
    print(f"{Fore.YELLOW}{'-'*80}")
    print(f"{Fore.GREEN}1{Style.RESET_ALL} - Загрузить прокси (файл + API)")
    print(f"{Fore.GREEN}2{Style.RESET_ALL} - Проверить прокси")
    print(f"{Fore.GREEN}3{Style.RESET_ALL} - Показать топ прокси")
    print(f"{Fore.GREEN}4{Style.RESET_ALL} - Выбрать прокси вручную")
    print(f"{Fore.GREEN}5{Style.RESET_ALL} - Показать текущий прокси")
    print(f"{Fore.GREEN}6{Style.RESET_ALL} - Показать статистику")
    print(f"{Fore.GREEN}7{Style.RESET_ALL} - Сохранить результаты")
    print(f"{Fore.GREEN}8{Style.RESET_ALL} - Загрузить из кэша")
    print(f"{Fore.GREEN}0{Style.RESET_ALL} - Выход")
    print(f"{Fore.YELLOW}{'-'*80}\n")


def handle_load_proxies():
    """Обработчик загрузки прокси"""
    print(f"\n{Fore.BLUE}📥 Загрузка прокси...\n")
    
    # Загрузка из файла
    file_proxies = loader.load_from_file(PROXIES_FILE)
    print(f"{Fore.GREEN}✓ Загружено из файла: {len(file_proxies)} прокси\n")
    
    # Загрузка из API
    print(f"{Fore.BLUE}⏳ Загрузка из API (может занять время)...\n")
    try:
        api_proxies = asyncio.run(loader.load_from_api())
        print(f"{Fore.GREEN}✓ Загружено из API: {len(api_proxies)} прокси\n")
    except Exception as e:
        print(f"{Fore.RED}✗ Ошибка при загрузке из API: {e}\n")
        api_proxies = []
    
    total = len(loader.get_all_proxies())
    print(f"{Fore.CYAN}{'='*80}")
    print(f"{Fore.GREEN}✓ Всего загружено прокси: {total}\n")


def handle_check_proxies():
    """Обработчик проверки прокси"""
    proxies = loader.get_all_proxies()
    
    if not proxies:
        print(f"{Fore.RED}✗ Сначала загрузите прокси!\n")
        return
    
    print(f"\n{Fore.BLUE}🔍 Проверка прокси (может занять 1-2 минуты)...\n")
    
    results = asyncio.run(checker.check_multiple(proxies))
    manager.add_results(results)
    
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.GREEN}✓ Проверка завершена!\n")
    
    # Показываем топ прокси
    manager.print_proxies(max_count=10)


def handle_show_best():
    """Обработчик показа лучших прокси"""
    if not manager.proxies:
        print(f"{Fore.RED}✗ Сначала проверьте прокси!\n")
        return
    
    best_proxy = manager.get_best_proxy()
    
    if best_proxy:
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"{Fore.GREEN}✓ ЛУЧШИЙ ПРОКСИ:")
        print(f"{Fore.YELLOW}  IP:PORT: {best_proxy.proxy}")
        print(f"{Fore.YELLOW}  Ping: {best_proxy.response_time:.2f} ms")
        print(f"{Fore.CYAN}{'='*80}\n")
    
    print(f"\n{Fore.YELLOW}ТОП-10 ПРОКСИ:\n")
    manager.print_proxies(max_count=10)


def handle_select_proxy():
    """Обработчик выбора прокси вручную"""
    proxies = manager.get_working_proxies()
    
    if not proxies:
        print(f"{Fore.RED}✗ Нет рабочих прокси!\n")
        return
    
    manager.print_proxies(max_count=20)
    
    try:
        index = int(input(f"{Fore.YELLOW}Введите номер прокси (1-{len(proxies)}): {Style.RESET_ALL}")) - 1
        
        if manager.select_proxy_by_index(index):
            proxy = manager.get_current_proxy()
            print(f"{Fore.GREEN}✓ Прокси выбран: {proxy}\n")
        else:
            print(f"{Fore.RED}✗ Неверный номер!\n")
    
    except ValueError:
        print(f"{Fore.RED}✗ Пожалуйста, введите число!\n")
    except Exception as e:
        print(f"{Fore.RED}✗ Ошибка: {e}\n")


def handle_show_current():
    """Обработчик показа текущего прокси"""
    current = manager.get_current_proxy()
    
    if current:
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"{Fore.GREEN}✓ ТЕКУЩИЙ ПРОКСИ:")
        print(f"{Fore.YELLOW}  {current}")
        print(f"{Fore.CYAN}{'='*80}\n")
    else:
        print(f"{Fore.RED}✗ Прокси не выбран. Используйте опцию 3 или 4.\n")


def handle_show_stats():
    """Обработчик показа статистики"""
    if not manager.proxies:
        print(f"{Fore.RED}✗ Данных нет. Сначала проверьте прокси!\n")
        return
    
    stats = manager.get_statistics()
    
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.YELLOW}{'СТАТИСТИКА':^80}")
    print(f"{Fore.CYAN}{'-'*80}")
    print(f"{Fore.GREEN}Всего проверено:        {stats['total']}")
    print(f"{Fore.GREEN}Работающих:             {stats['working']}")
    print(f"{Fore.GREEN}Не работающих:          {stats['not_working']}")
    print(f"{Fore.GREEN}Процент успеха:        {stats['success_rate']:.1f}%")
    print(f"{Fore.GREEN}Средний пинг:           {stats['avg_response_time']:.2f} ms")
    
    if stats['best_proxy']:
        print(f"{Fore.GREEN}Лучший прокси:          {stats['best_proxy']}")
        print(f"{Fore.GREEN}Пинг лучшего:           {stats['best_response_time']:.2f} ms")
    
    print(f"{Fore.CYAN}{'='*80}\n")


def handle_save_results():
    """Обработчик сохранения результатов"""
    if not manager.proxies:
        print(f"{Fore.RED}✗ Нет результатов для сохранения!\n")
        return
    
    manager.save_results()
    print(f"{Fore.GREEN}✓ Результаты сохранены!\n")


def handle_load_cache():
    """Обработчик загрузки из кэша"""
    if manager.load_from_cache():
        print(f"{Fore.GREEN}✓ Результаты загружены из кэша!\n")
        manager.print_proxies(max_count=5)
    else:
        print(f"{Fore.RED}✗ Не удалось загрузить кэш!\n")


def main():
    """Главная функция программы"""
    print_header()
    
    logger.info("Приложение запущено")
    
    # Пример создания файла с тестовыми прокси
    if not PROXIES_FILE.exists():
        print(f"{Fore.YELLOW}⚠️  Файл proxies.txt не найден. Создаю пример...\n")
        create_example_proxies_file()
    
    while True:
        try:
            print_menu()
            choice = input(f"{Fore.YELLOW}Выберите опцию (0-8): {Style.RESET_ALL}").strip()
            
            if choice == '1':
                handle_load_proxies()
            elif choice == '2':
                handle_check_proxies()
            elif choice == '3':
                handle_show_best()
            elif choice == '4':
                handle_select_proxy()
            elif choice == '5':
                handle_show_current()
            elif choice == '6':
                handle_show_stats()
            elif choice == '7':
                handle_save_results()
            elif choice == '8':
                handle_load_cache()
            elif choice == '0':
                print(f"\n{Fore.CYAN}👋 До свидания!\n")
                logger.info("Приложение завершено")
                sys.exit(0)
            else:
                print(f"{Fore.RED}✗ Неверный выбор. Попробуйте снова.\n")
        
        except KeyboardInterrupt:
            print(f"\n\n{Fore.CYAN}👋 До свидания!\n")
            logger.info("Приложение завершено пользователем")
            sys.exit(0)
        except Exception as e:
            print(f"{Fore.RED}✗ Ошибка: {e}\n")
            logger.error(f"Ошибка в главном цикле: {e}")


def create_example_proxies_file():
    """Создаёт пример файла с прокси"""
    example_proxies = """# Пример файла с прокси (формат: ip:port)
# Строки начинающиеся с # игнорируются

# Бесплатные открытые прокси (для примера, актуальность не гарантируется)
1.10.188.149:8080
1.32.59.217:47045
1.179.198.37:8080
103.153.232.182:8080
103.169.154.74:8080
103.199.84.122:23500
103.60.173.9:8080
104.223.123.98:8080
105.27.179.27:8080

# Добавьте свои прокси выше
"""
    
    try:
        with open(PROXIES_FILE, 'w', encoding='utf-8') as f:
            f.write(example_proxies)
        print(f"{Fore.GREEN}✓ Файл {PROXIES_FILE} создан\n")
    except Exception as e:
        print(f"{Fore.RED}✗ Ошибка при создании файла: {e}\n")


if __name__ == "__main__":
    main()
