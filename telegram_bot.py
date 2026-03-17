"""
Telegram бот для Proxy Manager с кнопками
"""
import asyncio
import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from telegram.constants import ChatAction

from proxy_loader import ProxyLoader
from proxy_checker import ProxyChecker
from proxy_manager import ProxyManager
from logger import setup_logger

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = setup_logger(__name__)

# Глобальные объекты
loader = ProxyLoader()
checker = ProxyChecker()
manager = ProxyManager()


def get_main_keyboard():
    """Главное меню с кнопками"""
    keyboard = [
        [
            InlineKeyboardButton("📥 Загрузить", callback_data="load"),
            InlineKeyboardButton("🔍 Проверить", callback_data="check"),
        ],
        [
            InlineKeyboardButton("⭐ Лучший", callback_data="best"),
            InlineKeyboardButton("🏆 Топ-10", callback_data="top"),
        ],
        [
            InlineKeyboardButton("📊 Статистика", callback_data="stats"),
            InlineKeyboardButton("💾 Сохранить", callback_data="save"),
        ],
        [
            InlineKeyboardButton("ℹ️ Помощь", callback_data="help"),
            InlineKeyboardButton("❌ Выход", callback_data="exit"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_keyboard():
    """Кнопка назад"""
    keyboard = [
        [InlineKeyboardButton("◀️ Назад в меню", callback_data="menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_load_keyboard():
    """Меню загрузки"""
    keyboard = [
        [
            InlineKeyboardButton("📁 Из файла", callback_data="load_file"),
            InlineKeyboardButton("🌐 Из API", callback_data="load_api"),
        ],
        [InlineKeyboardButton("📥 Оба сразу", callback_data="load_both")],
        [InlineKeyboardButton("◀️ Назад", callback_data="menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_check_keyboard():
    """Меню проверки"""
    proxies_count = len(loader.get_all_proxies())
    
    keyboard = [
        [
            InlineKeyboardButton(
                f"🔍 Проверить ({proxies_count})",
                callback_data="check_start"
            )
        ],
        [InlineKeyboardButton("◀️ Назад", callback_data="menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_top_keyboard():
    """Меню топ прокси"""
    keyboard = [
        [
            InlineKeyboardButton("🏆 Топ-5", callback_data="top_5"),
            InlineKeyboardButton("🏆 Топ-10", callback_data="top_10"),
        ],
        [
            InlineKeyboardButton("🏆 Топ-20", callback_data="top_20"),
            InlineKeyboardButton("🏆 Все", callback_data="top_all"),
        ],
        [InlineKeyboardButton("◀️ Назад", callback_data="menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /start - главное меню"""
    user = update.effective_user
    
    welcome_message = f"""
🌐 <b>Добро пожаловать в Proxy Manager!</b>

Я помогу тебе:
✅ Загружать прокси (файл + API)
✅ Проверять их работоспособность
✅ Находить лучшие по скорости
✅ Сохранять результаты

Выбери действие:
"""
    
    await update.message.reply_text(
        welcome_message,
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )
    
    logger.info(f"Пользователь {user.id} ({user.username}) запустил бота")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик всех кнопок"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # ==================== ГЛАВНОЕ МЕНЮ ====================
    if query.data == "menu":
        await query.edit_message_text(
            text="🌐 <b>Proxy Manager</b>\n\nВыбери действие:",
            reply_markup=get_main_keyboard(),
            parse_mode="HTML"
        )
    
    # ==================== МЕНЮ ЗАГРУЗКИ ====================
    elif query.data == "load":
        proxies_count = len(loader.get_all_proxies())
        text = f"""
📥 <b>ЗАГРУЗКА ПРОКСИ</b>

Текущие прокси загружены: {proxies_count}

Выбери источник:
"""
        await query.edit_message_text(
            text=text,
            reply_markup=get_load_keyboard(),
            parse_mode="HTML"
        )
    
    elif query.data == "load_file":
        await context.bot.send_chat_action(user_id, ChatAction.TYPING)
        try:
            file_proxies = loader.load_from_file()
            text = f"""
✅ <b>Загружено из файла</b>

📊 Прокси: {len(file_proxies)}

Теперь можешь проверить их!
"""
            await query.edit_message_text(
                text=text,
                reply_markup=get_load_keyboard(),
                parse_mode="HTML"
            )
            logger.info(f"Пользователь {user_id} загрузил {len(file_proxies)} из файла")
        except Exception as e:
            await query.edit_message_text(
                text=f"❌ <b>Ошибка</b>\n\n{str(e)}",
                reply_markup=get_load_keyboard(),
                parse_mode="HTML"
            )
    
    elif query.data == "load_api":
        await context.bot.send_chat_action(user_id, ChatAction.TYPING)
        try:
            api_proxies = await loader.load_from_api()
            text = f"""
✅ <b>Загружено из API</b>

📊 Прокси: {len(api_proxies)}

Теперь можешь проверить их!
"""
            await query.edit_message_text(
                text=text,
                reply_markup=get_load_keyboard(),
                parse_mode="HTML"
            )
            logger.info(f"Пользователь {user_id} загрузил {len(api_proxies)} из API")
        except Exception as e:
            await query.edit_message_text(
                text=f"❌ <b>Ошибка при загрузке из API</b>\n\n{str(e)}",
                reply_markup=get_load_keyboard(),
                parse_mode="HTML"
            )
    
    elif query.data == "load_both":
        await context.bot.send_chat_action(user_id, ChatAction.TYPING)
        try:
            file_proxies = loader.load_from_file()
            api_proxies = await loader.load_from_api()
            total = len(loader.get_all_proxies())
            
            text = f"""
✅ <b>Прокси загружены!</b>

📊 Из файла: {len(file_proxies)}
📊 Из API: {len(api_proxies)}
📊 <b>Всего: {total}</b>

Дальше нажми 🔍 Проверить!
"""
            await query.edit_message_text(
                text=text,
                reply_markup=get_main_keyboard(),
                parse_mode="HTML"
            )
            logger.info(f"Пользователь {user_id} загрузил {total} прокси")
        except Exception as e:
            await query.edit_message_text(
                text=f"❌ <b>Ошибка</b>\n\n{str(e)}",
                reply_markup=get_load_keyboard(),
                parse_mode="HTML"
            )
    
    # ==================== ПРОВЕРКА ПРОКСИ ====================
    elif query.data == "check":
        proxies = loader.get_all_proxies()
        if not proxies:
            text = """
❌ <b>Нет прокси для проверки!</b>

Сначала загрузи прокси (📥 Загрузить)
"""
            await query.edit_message_text(
                text=text,
                reply_markup=get_main_keyboard(),
                parse_mode="HTML"
            )
            return
        
        text = f"""
🔍 <b>ПРОВЕРКА ПРОКСИ</b>

Готово �� проверке: {len(proxies)} прокси

⏱️ Это займёт 1-2 минуты...

Нажми кнопку ниже:
"""
        await query.edit_message_text(
            text=text,
            reply_markup=get_check_keyboard(),
            parse_mode="HTML"
        )
    
    elif query.data == "check_start":
        proxies = loader.get_all_proxies()
        
        await query.edit_message_text(
            text="⏳ <b>Проверяю прокси...</b>\n\nПожалуйста, подожди...",
            parse_mode="HTML"
        )
        
        try:
            await context.bot.send_chat_action(user_id, ChatAction.TYPING)
            results = await checker.check_multiple(proxies)
            manager.add_results(results)
            
            working = len(manager.get_working_proxies())
            success_rate = (working / len(results) * 100) if results else 0
            
            text = f"""
✅ <b>ПРОВЕРКА ЗАВЕРШЕНА!</b>

📊 <b>Результаты:</b>
• Проверено: {len(results)}
• ✅ Работающих: {working}
• ❌ Не работает: {len(results) - working}
• 📈 Успех: {success_rate:.1f}%

Теперь смотри результаты!
"""
            await query.edit_message_text(
                text=text,
                reply_markup=get_main_keyboard(),
                parse_mode="HTML"
            )
            logger.info(f"Пользователь {user_id} проверил {len(results)} прокси")
        except Exception as e:
            await query.edit_message_text(
                text=f"❌ <b>Ошибка при проверке</b>\n\n{str(e)}",
                reply_markup=get_main_keyboard(),
                parse_mode="HTML"
            )
    
    # ==================== ЛУЧШИЙ ПРОКСИ ====================
    elif query.data == "best":
        if not manager.proxies:
            text = """
❌ <b>Нет проверенных прокси!</b>

Сначала:
1️⃣ 📥 Загрузить
2️⃣ 🔍 Проверить
"""
            await query.edit_message_text(
                text=text,
                reply_markup=get_main_keyboard(),
                parse_mode="HTML"
            )
            return
        
        best = manager.get_best_proxy()
        if best:
            text = f"""
⭐ <b>ЛУЧШИЙ ПРОКСИ</b>

🔗 <code>{best.proxy}</code>

⚡ Ping: <b>{best.response_time:.2f} ms</b>
✅ Статус: <b>Работает</b>
"""
            keyboard = [
                [InlineKeyboardButton("◀️ Назад", callback_data="menu")]
            ]
            await query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML"
            )
        else:
            await query.edit_message_text(
                text="❌ <b>Нет рабочих прокси!</b>",
                reply_markup=get_main_keyboard(),
                parse_mode="HTML"
            )
    
    # ==================== ТОП ПРОКСИ ====================
    elif query.data == "top":
        if not manager.proxies:
            text = """
❌ <b>Нет проверенных прокси!</b>

Сначала проверь прокси (🔍 Проверить)
"""
            await query.edit_message_text(
                text=text,
                reply_markup=get_main_keyboard(),
                parse_mode="HTML"
            )
            return
        
        text = "🏆 <b>ТОП ПРОКСИ</b>\n\nВыбери количество:"
        await query.edit_message_text(
            text=text,
            reply_markup=get_top_keyboard(),
            parse_mode="HTML"
        )
    
    elif query.data.startswith("top_"):
        count_map = {
            "top_5": 5,
            "top_10": 10,
            "top_20": 20,
            "top_all": 999
        }
        count = count_map.get(query.data, 10)
        top = manager.get_top_proxies(count)
        
        if not top:
            text = "❌ <b>Нет рабочих прокси!</b>"
        else:
            text = f"🏆 <b>ТОП-{len(top)} ПРОКСИ</b>\n\n"
            for i, proxy in enumerate(top, 1):
                text += f"{i}. <code>{proxy.proxy}</code>\n"
                text += f"   ⚡ {proxy.response_time:.2f}ms\n\n"
        
        await query.edit_message_text(
            text=text,
            reply_markup=get_top_keyboard(),
            parse_mode="HTML"
        )
    
    # ==================== СТАТИСТИКА ====================
    elif query.data == "stats":
        if not manager.proxies:
            text = """
❌ <b>Нет данных!</b>

Сначала проверь прокси (🔍 Проверить)
"""
            await query.edit_message_text(
                text=text,
                reply_markup=get_main_keyboard(),
                parse_mode="HTML"
            )
            return
        
        stats = manager.get_statistics()
        text = f"""
📊 <b>СТАТИСТИКА</b>

📈 Всего проверено: <b>{stats['total']}</b>
✅ Работающих: <b>{stats['working']}</b>
❌ Не работает: <b>{stats['not_working']}</b>
📉 Успех: <b>{stats['success_rate']:.1f}%</b>

⚡ <b>Средний пинг:</b> {stats['avg_response_time']:.2f} ms

⭐ <b>Лучший:</b> <code>{stats['best_proxy']}</code>
🚀 <b>Его пинг:</b> {stats['best_response_time']:.2f} ms
"""
        await query.edit_message_text(
            text=text,
            reply_markup=get_back_keyboard(),
            parse_mode="HTML"
        )
    
    # ==================== СОХРАНИТЬ ====================
    elif query.data == "save":
        if not manager.proxies:
            text = """
❌ <b>Нет результатов для сохранения!</b>

Сначала проверь прокси (🔍 Проверить)
"""
            await query.edit_message_text(
                text=text,
                reply_markup=get_main_keyboard(),
                parse_mode="HTML"
            )
            return
        
        try:
            manager.save_results()
            text = """
✅ <b>РЕЗУЛЬТАТЫ СОХРАНЕНЫ!</b>

📁 Файл: results.json

Все результаты сохранены!
"""
            await query.edit_message_text(
                text=text,
                reply_markup=get_main_keyboard(),
                parse_mode="HTML"
            )
            logger.info(f"Пользователь {user_id} сохранил результаты")
        except Exception as e:
            await query.edit_message_text(
                text=f"❌ <b>Ошибка при сохранении</b>\n\n{str(e)}",
                reply_markup=get_main_keyboard(),
                parse_mode="HTML"
            )
    
    # ==================== ПОМОЩЬ ====================
    elif query.data == "help":
        text = """
ℹ️ <b>КАК ПОЛЬЗОВАТЬСЯ?</b>

<b>Шаг 1:</b> 📥 Загрузить
• Загрузи прокси из файла или API

<b>Шаг 2:</b> 🔍 Проверить
• Проверь их работоспособность

<b>Шаг 3:</b> ⭐ Лучший или 🏆 Топ
• Выбери лучшие прокси

<b>Шаг 4:</b> 📊 Статистика
• Посмотри результаты

<b>Шаг 5:</b> 💾 Сохранить
• Сохрани в файл
"""
        await query.edit_message_text(
            text=text,
            reply_markup=get_back_keyboard(),
            parse_mode="HTML"
        )
    
    # ==================== ВЫХОД ====================
    elif query.data == "exit":
        await query.edit_message_text(
            text="👋 <b>До свидания!</b>\n\nНажми /start чтобы начать заново",
            reply_markup=None,
            parse_mode="HTML"
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /help"""
    text = """
ℹ️ <b>PROXY MANAGER БОТ</b>

<b>Основной процесс:</b>

1️⃣ <b>Загрузи прокси</b> (📥 Загрузить)
2️⃣ <b>Проверь</b> (🔍 Проверить)
3️⃣ <b>Выбери лучшие</b> (⭐ или 🏆)
4️⃣ <b>Смотри статистику</b> (📊)
5️⃣ <b>Сохрани</b> (💾)

/start - Главное меню
"""
    
    await update.message.reply_text(text, parse_mode="HTML")


def main() -> None:
    """Запуск бота"""
    # Получи токен из переменной окружения
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    
    if not TOKEN:
        print("❌ ОШИБКА: Переменная TELEGRAM_TOKEN не установлена!")
        print("Установи её и запусти снова.")
        return
    
    # Создаём приложение
    application = Application.builder().token(TOKEN).build()
    
    # Регистрируем команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # Регистрируем обработчик кнопок
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Запускаем бота
    logger.info("🤖 Бот запущен!")
    print("🤖 Telegram бот Proxy Manager запущен!")
    print("Нажми Ctrl+C чтобы остановить")
    
    application.run_polling()


if __name__ == '__main__':
    main()
