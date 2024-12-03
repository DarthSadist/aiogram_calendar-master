import logging
import asyncio
import sys
from datetime import datetime, timedelta
from typing import Optional, Tuple

import locale
from logging.handlers import RotatingFileHandler

from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback, DialogCalendar, DialogCalendarCallback
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
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
                KeyboardButton(text='⚡️ Быстрые даты'),
                KeyboardButton(text='⚙️ Настройки')
            ]
        ]
        return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

    @staticmethod
    def get_quick_dates_keyboard() -> ReplyKeyboardMarkup:
        """Создает клавиатуру быстрых дат"""
        kb = [
            [
                KeyboardButton(text='📌 Сегодня'),
                KeyboardButton(text='📌 Завтра')
            ],
            [
                KeyboardButton(text='📌 Через неделю'),
                KeyboardButton(text='📌 Через 2 недели')
            ],
            [
                KeyboardButton(text='📌 Через месяц'),
                KeyboardButton(text='📌 Через 3 месяца')
            ],
            [
                KeyboardButton(text='📌 Начало месяца'),
                KeyboardButton(text='📌 Конец месяца')
            ],
            [
                KeyboardButton(text='🔙 Вернуться в главное меню')
            ]
        ]
        return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# Добавляем класс для работы с настройками
class UserSettings:
    """Класс для управления настройками пользователя"""
    
    DATE_FORMATS = {
        "DD.MM.YYYY": "%d.%m.%Y",
        "YYYY-MM-DD": "%Y-%m-%d",
        "MM/DD/YYYY": "%m/%d/%Y"
    }

    @staticmethod
    def get_settings_keyboard() -> InlineKeyboardMarkup:
        """Создает клавиатуру настроек"""
        keyboard = [
            [
                InlineKeyboardButton(text="🌍 Изменить язык", callback_data="settings_language"),
                InlineKeyboardButton(text="📅 Формат даты", callback_data="settings_date_format")
            ],
            [
                InlineKeyboardButton(text="🔙 Вернуться в главное меню", callback_data="back_to_main")
            ]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def get_date_format_keyboard() -> InlineKeyboardMarkup:
        """Создает клавиатуру выбора формата даты"""
        keyboard = [
            [InlineKeyboardButton(text="DD.MM.YYYY", callback_data="date_format_dd.mm.yyyy")],
            [InlineKeyboardButton(text="YYYY-MM-DD", callback_data="date_format_yyyy-mm-dd")],
            [InlineKeyboardButton(text="MM/DD/YYYY", callback_data="date_format_mm/dd/yyyy")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_settings")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

class QuickDates:
    """Класс для работы с быстрыми датами"""

    @staticmethod
    def get_quick_dates_keyboard() -> ReplyKeyboardMarkup:
        """Создает клавиатуру быстрых дат"""
        kb = [
            [
                KeyboardButton(text='📌 Сегодня'),
                KeyboardButton(text='📌 Завтра')
            ],
            [
                KeyboardButton(text='📌 Через неделю'),
                KeyboardButton(text='📌 Через 2 недели')
            ],
            [
                KeyboardButton(text='📌 Через месяц'),
                KeyboardButton(text='📌 Через 3 месяца')
            ],
            [
                KeyboardButton(text='📌 Начало месяца'),
                KeyboardButton(text='📌 Конец месяца')
            ],
            [
                KeyboardButton(text='🔙 Вернуться в главное меню')
            ]
        ]
        return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

    @staticmethod
    def get_date_description(date: datetime) -> str:
        """Возвращает описание даты с днем недели и остальной информацией"""
        weekdays = {
            0: 'понедельник',
            1: 'вторник',
            2: 'среда',
            3: 'четверг',
            4: 'пятница',
            5: 'суббота',
            6: 'воскресенье'
        }
        
        day_of_week = weekdays[date.weekday()]
        days_until = (date - datetime.now()).days
        
        if days_until == 0:
            relative_date = "сегодня"
        elif days_until == 1:
            relative_date = "завтра"
        else:
            relative_date = f"через {days_until} дней"
            
        return (f"📅 Дата: {date.strftime('%d.%m.%Y')}\n"
                f"📆 День недели: {day_of_week}\n"
                f"⏳ Когда: {relative_date}\n"
                f"📊 Это {date.timetuple().tm_yday}-й день года\n"
                f"📈 Прошло недель с начала года: {date.isocalendar()[1]}")

# Создание клавиатур
start_kb = CalendarKeyboards.get_start_keyboard()
quick_dates_kb = QuickDates.get_quick_dates_keyboard()

@dp.message(Command("start"))
async def command_start_handler(message: Message) -> None:
    """Обработчик команды /start"""
    try:
        user_name = message.from_user.full_name
        logger.info(f"Пользователь {user_name} ({message.from_user.id}) запустил бота")
        
        await message.answer(
            f"👋 Привет, {hbold(user_name)}!\n\n"
            f"🤖 Я бот-календарь, который поможет тебе выбрать нужную дату.\n\n"
            f"✨ У меня есть несколько типов календарей:\n"
            f"📅 Простой - для быстрого выбора даты\n"
            f"📆 Расширенный - с выбором месяца\n"
            f"🗓 Диалоговый - пошаговый выбор\n"
            f"⚡️ Быстрые даты - для частых вариантов\n\n"
            f"❔ Используйте /help для получения справки\n"
            f"⚙️ Используйте /settings для настройки бота\n\n"
            f"🎯 Выберите удобный для вас тип календаря:",
            reply_markup=start_kb
        )
    except Exception as e:
        logger.error(f"Ошибка в обработчике /start: {e}")
        await message.answer("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")

@dp.message(Command("help"))
async def command_help_handler(message: Message) -> None:
    """Обработчик команды /help"""
    try:
        await message.answer(
            "📚 Справка по использованию бота:\n\n"
            "🔹 /start - Запуск бота и показ главного меню\n"
            "🔹 /help - Показ этой справки\n"
            "🔹 /settings - Настройки бота\n\n"
            "📅 Типы календарей:\n"
            "1️⃣ Простой календарь - выбор даты в один клик\n"
            "2️⃣ Расширенный календарь - с навигацией по месяцам\n"
            "3️⃣ Диалоговый календарь - пошаговый выбор\n"
            "4️⃣ Быстрые даты - популярные варианты\n\n"
            "⚙️ В настройках вы можете:\n"
            "- Изменить формат отображения даты\n"
            "- Выбрать язык интерфейса\n\n"
            "❓ Если у вас возникли вопросы или проблемы,\n"
            "пожалуйста, свяжитесь с поддержкой"
        )
    except Exception as e:
        logger.error(f"Ошибка в обработчике /help: {e}")
        await message.answer("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")

@dp.message(Command("settings"))
async def command_settings_handler(message: Message) -> None:
    """Обработчик команды /settings"""
    try:
        await message.answer(
            "⚙️ Настройки бота\n\n"
            "Выберите, что хотите настроить:",
            reply_markup=UserSettings.get_settings_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка в обработчике /settings: {e}")
        await message.answer("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")

@dp.message(F.text == "⚙️ Настройки")
async def settings_handler(message: Message) -> None:
    """Обработчик кнопки настроек в главном меню"""
    try:
        await message.answer(
            "⚙️ Настройки бота\n\n"
            "Выберите, что хотите настроить:",
            reply_markup=UserSettings.get_settings_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка в обработчике настроек: {e}")
        await message.answer("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")

@dp.message(F.text == "⚡️ Быстрые даты")
async def quick_dates_handler(message: Message) -> None:
    """
    Обработчик быстрых дат
    
    Показывает меню быстрого выбора дат с различными вариантами:
    - Сегодня/Завтра
    - Через неделю/две недели
    - Через месяц/три месяца
    - Начало/конец текущего месяца
    """
    try:
        await message.answer(
            "⚡️ Быстрый выбор даты\n\n"
            "📍 Выберите один из вариантов:\n\n"
            "• Сегодня/Завтра - для ближайших дат\n"
            "• Через неделю/две - для планирования на недели\n"
            "• Через месяц/три - для долгосрочного планирования\n"
            "• Начало/конец месяца - для работы с границами месяца",
            reply_markup=quick_dates_kb
        )
    except Exception as e:
        logger.error(f"Ошибка в обработчике быстрых дат: {e}")
        await message.answer("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")

@dp.message(F.text == "📌 Сегодня")
async def today_handler(message: Message) -> None:
    """Обработчик выбора сегодняшней даты"""
    try:
        today = datetime.now()
        await message.answer(
            f"✅ Выбрана дата:\n\n{QuickDates.get_date_description(today)}\n\n"
            f"📝 Можете выбрать другую дату или вернуться в главное меню",
            reply_markup=quick_dates_kb
        )
    except Exception as e:
        logger.error(f"Ошибка в обработчике сегодняшней даты: {e}")
        await message.answer("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")

@dp.message(F.text == "📌 Завтра")
async def tomorrow_handler(message: Message) -> None:
    """Обработчик выбора завтрашней даты"""
    try:
        tomorrow = datetime.now() + timedelta(days=1)
        await message.answer(
            f"✅ Выбрана дата:\n\n{QuickDates.get_date_description(tomorrow)}\n\n"
            f"📝 Можете выбрать другую дату или вернуться в главное меню",
            reply_markup=quick_dates_kb
        )
    except Exception as e:
        logger.error(f"Ошибка в обработчике завтрашней даты: {e}")
        await message.answer("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")

@dp.message(F.text == "📌 Через неделю")
async def next_week_handler(message: Message) -> None:
    """Обработчик выбора даты через неделю"""
    try:
        next_week = datetime.now() + timedelta(days=7)
        await message.answer(
            f"✅ Выбрана дата:\n\n{QuickDates.get_date_description(next_week)}\n\n"
            f"📝 Можете выбрать другую дату или вернуться в главное меню",
            reply_markup=quick_dates_kb
        )
    except Exception as e:
        logger.error(f"Ошибка в обработчике даты через неделю: {e}")
        await message.answer("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")

@dp.message(F.text == "📌 Через 2 недели")
async def two_weeks_handler(message: Message) -> None:
    """Обработчик выбора даты через 2 недели"""
    try:
        two_weeks = datetime.now() + timedelta(days=14)
        await message.answer(
            f"✅ Выбрана дата:\n\n{QuickDates.get_date_description(two_weeks)}\n\n"
            f"📝 Можете выбрать другую дату или вернуться в главное меню",
            reply_markup=quick_dates_kb
        )
    except Exception as e:
        logger.error(f"Ошибка в обработчике даты через 2 недели: {e}")
        await message.answer("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")

@dp.message(F.text == "📌 Через месяц")
async def next_month_handler(message: Message) -> None:
    """Обработчик выбора даты через месяц"""
    try:
        next_month = datetime.now() + timedelta(days=30)
        await message.answer(
            f"✅ Выбрана дата:\n\n{QuickDates.get_date_description(next_month)}\n\n"
            f"📝 Можете выбрать другую дату или вернуться в главное меню",
            reply_markup=quick_dates_kb
        )
    except Exception as e:
        logger.error(f"Ошибка в обработчике даты через месяц: {e}")
        await message.answer("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")

@dp.message(F.text == "📌 Через 3 месяца")
async def three_months_handler(message: Message) -> None:
    """Обработчик выбора даты через 3 месяца"""
    try:
        three_months = datetime.now() + timedelta(days=90)
        await message.answer(
            f"✅ Выбрана дата:\n\n{QuickDates.get_date_description(three_months)}\n\n"
            f"📝 Можете выбрать другую дату или вернуться в главное меню",
            reply_markup=quick_dates_kb
        )
    except Exception as e:
        logger.error(f"Ошибка в обработчике даты через 3 месяца: {e}")
        await message.answer("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")

@dp.message(F.text == "📌 Начало месяца")
async def start_of_month_handler(message: Message) -> None:
    """Обработчик выбора начала текущего месяца"""
    try:
        today = datetime.now()
        start_of_month = today.replace(day=1)
        await message.answer(
            f"✅ Выбрана дата:\n\n{QuickDates.get_date_description(start_of_month)}\n\n"
            f"📝 Можете выбрать другую дату или вернуться в главное меню",
            reply_markup=quick_dates_kb
        )
    except Exception as e:
        logger.error(f"Ошибка в обработчике начала месяца: {e}")
        await message.answer("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")

@dp.message(F.text == "📌 Конец месяца")
async def end_of_month_handler(message: Message) -> None:
    """Обработчик выбора конца текущего месяца"""
    try:
        today = datetime.now()
        # Получаем последний день текущего месяца
        if today.month == 12:
            last_day = today.replace(day=31)
        else:
            last_day = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        
        await message.answer(
            f"✅ Выбрана дата:\n\n{QuickDates.get_date_description(last_day)}\n\n"
            f"📝 Можете выбрать другую дату или вернуться в главное меню",
            reply_markup=quick_dates_kb
        )
    except Exception as e:
        logger.error(f"Ошибка в обработчике конца месяца: {e}")
        await message.answer("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")

@dp.message(F.text == "🔙 Вернуться в главное меню")
async def back_to_main_handler(message: Message) -> None:
    """Обработчик возврата в главное меню"""
    try:
        await message.answer(
            "🏠 Главное меню\n"
            "Выберите тип календаря:",
            reply_markup=start_kb
        )
    except Exception as e:
        logger.error(f"Ошибка в обработчике возврата в главное меню: {e}")
        await message.answer("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")

@dp.callback_query(F.data == "settings_language")
async def process_language_setting(callback_query: CallbackQuery) -> None:
    """Обработчик настройки языка"""
    try:
        await callback_query.message.edit_text(
            "🌍 Выбор языка\n\n"
            "🚧 Эта функция находится в разработке.\n"
            "В данный момент доступен только русский язык."
        )
    except Exception as e:
        logger.error(f"Ошибка в обработчике настройки языка: {e}")
        await callback_query.message.answer("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")

@dp.callback_query(F.data == "settings_date_format")
async def process_date_format_setting(callback_query: CallbackQuery) -> None:
    """Обработчик настройки формата даты"""
    try:
        await callback_query.message.edit_text(
            "📅 Выберите формат даты:",
            reply_markup=UserSettings.get_date_format_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка в обработчике настройки формата даты: {e}")
        await callback_query.message.answer("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")

@dp.callback_query(F.data == "back_to_main")
async def process_back_to_main(callback_query: CallbackQuery) -> None:
    """Обработчик возврата в главное меню из настроек"""
    try:
        await callback_query.message.answer(
            "🏠 Главное меню\n"
            "Выберите тип календаря:",
            reply_markup=start_kb
        )
        await callback_query.message.delete()
    except Exception as e:
        logger.error(f"Ошибка при возврате в главное меню: {e}")
        await callback_query.message.answer("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")

@dp.callback_query(F.data == "back_to_settings")
async def process_back_to_settings(callback_query: CallbackQuery) -> None:
    """Обработчик возврата в меню настроек"""
    try:
        await callback_query.message.edit_text(
            "⚙️ Настройки бота\n\n"
            "Выберите, что хотите настроить:",
            reply_markup=UserSettings.get_settings_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка при возврате в настройки: {e}")
        await callback_query.message.answer("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")

@dp.callback_query(F.data.startswith("date_format_"))
async def process_date_format_selection(callback_query: CallbackQuery) -> None:
    """Обработчик выбора формата даты"""
    try:
        format_type = callback_query.data.replace("date_format_", "")
        format_display = {
            "dd.mm.yyyy": "DD.MM.YYYY",
            "yyyy-mm-dd": "YYYY-MM-DD",
            "mm/dd/yyyy": "MM/DD/YYYY"
        }.get(format_type, "DD.MM.YYYY")
        
        await callback_query.message.edit_text(
            f"✅ Формат даты изменен на: {format_display}\n"
            f"Теперь даты будут отображаться в этом формате.",
            reply_markup=UserSettings.get_settings_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка при выборе формата даты: {e}")
        await callback_query.message.answer("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")

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
