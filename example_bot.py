import logging
import asyncio
import sys
from datetime import datetime
from typing import Optional, Tuple

import locale
from logging.handlers import RotatingFileHandler

from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback, DialogCalendar, DialogCalendarCallback
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.filters.callback_data import CallbackData
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, CallbackQuery
from aiogram.utils.markdown import hbold
from aiogram.client.default import DefaultBotProperties

from bot_config import API_TOKEN

# Настройка логирования
def setup_logging() -> None:
    """Настройка системы логирования"""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            RotatingFileHandler(
                "bot.log",
                maxBytes=10485760,  # 10MB
                backupCount=5,
                encoding="utf-8"
            ),
            logging.StreamHandler(sys.stdout)
        ]
    )

# Инициализация логгера
logger = logging.getLogger(__name__)

try:
    locale.setlocale(locale.LC_ALL, 'ru_RU.utf8')
except locale.Error as e:
    logger.warning(f"Не удалось установить русскую локаль: {e}")

# Инициализация диспетчера
dp = Dispatcher()

# Клавиатура с календарями
class CalendarKeyboards:
    """Класс для управления клавиатурами календаря"""
    
    @staticmethod
    def get_start_keyboard() -> ReplyKeyboardMarkup:
        """Создает и возвращает стартовую клавиатуру"""
        kb = [
            [
                KeyboardButton(text='📅 Простой календарь'),
                KeyboardButton(text='📆 Расширенный календарь'),
            ],
            [
                KeyboardButton(text='🗓 Диалоговый календарь'),
                KeyboardButton(text='📊 Календарь с годом'),
            ],
            [
                KeyboardButton(text='📋 Календарь с месяцем')
            ]
        ]
        return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# Создание клавиатуры
start_kb = CalendarKeyboards.get_start_keyboard()

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    Обработчик команды /start
    
    Args:
        message (Message): Входящее сообщение
    """
    try:
        user_name = message.from_user.full_name
        logger.info(f"Пользователь {user_name} ({message.from_user.id}) запустил бота")
        
        await message.answer(
            f"👋 Привет, {hbold(user_name)}!\n\n"
            f"🤖 Я бот-календарь, который поможет тебе выбрать нужную дату.\n\n"
            f"✨ У меня есть несколько типов календарей:\n"
            f"📅 Простой - для быстрого выбора даты\n"
            f"📆 Расширенный - с выбором месяца\n"
            f"🗓 Диалоговый - пошаговый выбор\n\n"
            f"🎯 Выберите удобный для вас тип календаря:",
            reply_markup=start_kb
        )
    except Exception as e:
        logger.error(f"Ошибка в обработчике /start: {e}")
        await message.answer("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")

@dp.message(F.text == "📅 Простой календарь")
async def nav_cal_handler(message: Message) -> None:
    """
    Обработчик для простого календаря
    
    Args:
        message (Message): Входящее сообщение
    """
    try:
        logger.info(f"Пользователь {message.from_user.id} открыл простой календарь")
        await message.answer(
            "📅 Выберите дату в календаре: ",
            reply_markup=await SimpleCalendar().start_calendar()
        )
    except Exception as e:
        logger.error(f"Ошибка при создании простого календаря: {e}")
        await message.answer("❌ Не удалось создать календарь. Попробуйте позже.")

@dp.message(F.text == "📆 Расширенный календарь")
async def nav_cal_handler_date(message: Message) -> None:
    """
    Обработчик для календаря с выбором месяца
    
    Args:
        message (Message): Входящее сообщение
    """
    try:
        calendar = SimpleCalendar()
        calendar.set_dates_range(datetime(2022, 1, 1), datetime(2025, 12, 31))
        logger.info(f"Пользователь {message.from_user.id} открыл календарь с выбором месяца")
        
        await message.answer(
            "📆 Календарь открыт на текущий месяц\n"
            "✨ Выберите любую дату с 2022 по 2025 год:",
            reply_markup=await calendar.start_calendar(year=2024, month=2)
        )
    except Exception as e:
        logger.error(f"Ошибка при создании календаря с выбором месяца: {e}")
        await message.answer("❌ Не удалось создать календарь. Попробуйте позже.")

@dp.callback_query(SimpleCalendarCallback.filter())
async def process_simple_calendar(callback_query: CallbackQuery, callback_data: CallbackData) -> None:
    """
    Обработчик callback-запросов для простого календаря
    
    Args:
        callback_query (CallbackQuery): Callback-запрос
        callback_data (CallbackData): Данные callback-запроса
    """
    try:
        calendar = SimpleCalendar(show_alerts=True)
        calendar.set_dates_range(datetime(2022, 1, 1), datetime(2025, 12, 31))

        selected, date = await calendar.process_selection(callback_query, callback_data)
        if selected:
            logger.info(f"Пользователь {callback_query.from_user.id} выбрал дату: {date}")
            await callback_query.message.answer(
                f'✅ Выбрана дата: {date.strftime("%d.%m.%Y")}\n'
                f'📝 Можете выбрать другую дату или вернуться в главное меню'
            )
    except Exception as e:
        logger.error(f"Ошибка при обработке выбора даты: {e}")
        await callback_query.message.answer("❌ Произошла ошибка при выборе даты.")

@dp.message(F.text == "🗓 Диалоговый календарь")
async def dialog_cal_handler(message: Message) -> None:
    """
    Обработчик для диалогового календаря
    
    Args:
        message (Message): Входящее сообщение
    """
    try:
        logger.info(f"Пользователь {message.from_user.id} открыл диалоговый календарь")
        await message.answer(
            "🗓 Выберите дату пошагово:\n"
            "1️⃣ Сначала выберите год\n"
            "2️⃣ Затем месяц\n"
            "3️⃣ И наконец день",
            reply_markup=await DialogCalendar().start_calendar()
        )
    except Exception as e:
        logger.error(f"Ошибка при создании диалогового календаря: {e}")
        await message.answer("❌ Не удалось создать календарь. Попробуйте позже.")

@dp.message(F.text == "📊 Календарь с годом")
async def dialog_cal_handler_year(message: Message) -> None:
    """
    Обработчик для диалогового календаря с указанным годом
    
    Args:
        message (Message): Входящее сообщение
    """
    try:
        logger.info(f"Пользователь {message.from_user.id} открыл диалоговый календарь с годом")
        await message.answer(
            "📊 Выберите дату, начиная с 1989 года:\n"
            "1️⃣ Выберите год (с 1989)\n"
            "2️⃣ Выберите месяц\n"
            "3️⃣ Выберите день",
            reply_markup=await DialogCalendar().start_calendar(year=1989)
        )
    except Exception as e:
        logger.error(f"Ошибка при создании диалогового календаря с годом: {e}")
        await message.answer("❌ Не удалось создать календарь. Попробуйте позже.")

@dp.message(F.text == "📋 Календарь с месяцем")
async def dialog_cal_handler_month(message: Message) -> None:
    """
    Обработчик для диалогового календаря с указанным месяцем
    
    Args:
        message (Message): Входящее сообщение
    """
    try:
        logger.info(f"Пользователь {message.from_user.id} открыл диалоговый календарь с месяцем")
        await message.answer(
            "📋 Выберите дату, начиная с июня 1989:\n"
            "1️⃣ Выберите год (с 1989)\n"
            "2️⃣ Выберите месяц (начиная с июня)\n"
            "3️⃣ Выберите день",
            reply_markup=await DialogCalendar().start_calendar(year=1989, month=6)
        )
    except Exception as e:
        logger.error(f"Ошибка при создании диалогового календаря с месяцем: {e}")
        await message.answer("❌ Не удалось создать календарь. Попробуйте позже.")

@dp.callback_query(DialogCalendarCallback.filter())
async def process_dialog_calendar(callback_query: CallbackQuery, callback_data: CallbackData) -> None:
    """
    Обработчик callback-запросов для диалогового календаря
    
    Args:
        callback_query (CallbackQuery): Callback-запрос
        callback_data (CallbackData): Данные callback-запроса
    """
    try:
        selected, date = await DialogCalendar().process_selection(callback_query, callback_data)
        if selected:
            logger.info(f"Пользователь {callback_query.from_user.id} выбрал дату: {date}")
            await callback_query.message.answer(
                f'✅ Выбрана дата: {date.strftime("%d.%m.%Y")}\n'
                f'📝 Можете выбрать другую дату или вернуться в главное меню'
            )
    except Exception as e:
        logger.error(f"Ошибка при обработке выбора даты: {e}")
        await callback_query.message.answer("❌ Произошла ошибка при выборе даты.")

async def main() -> None:
    """
    Основная функция запуска бота
    """
    try:
        # Инициализация бота с настройками по умолчанию
        bot = Bot(API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        
        logger.info("Бот запущен")
        
        # Запуск процесса обработки событий
        await dp.start_polling(bot)
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске бота: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_logging()
    asyncio.run(main())
