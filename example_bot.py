from datetime import datetime
import logging
import sys
import asyncio
from typing import Dict

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from aiogram_calendar import SimpleCalendar, DialogCalendar
from aiogram_calendar.simple_calendar import SimpleCalendarCallback
from aiogram_calendar.dialog_calendar import DialogCalendarCallback

from bot_config import API_TOKEN

# Enable logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Dictionary to store user settings
user_settings: Dict[int, 'UserSettings'] = {}

# Available date formats
DATE_FORMATS = {
    'dd.mm.yyyy': '%d.%m.%Y',
    'yyyy-mm-dd': '%Y-%m-%d',
    'mm/dd/yyyy': '%m/%d/%Y'
}

class UserSettings:
    """Класс для управления настройками пользователя"""
    def __init__(self):
        self.language = 'ru'  # Язык по умолчанию
        self.date_format = 'dd.mm.yyyy'  # Формат даты по умолчанию

    @staticmethod
    def get_language_keyboard() -> InlineKeyboardMarkup:
        """Создает клавиатуру выбора языка"""
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text='🇷🇺 Русский', callback_data='lang_ru'),
                InlineKeyboardButton(text='🇬🇧 English', callback_data='lang_en')
            ],
            [InlineKeyboardButton(text='🔙 Назад/Back', callback_data='back_to_settings')]
        ])
        return kb

    def get_settings_keyboard(self) -> InlineKeyboardMarkup:
        """Создает клавиатуру настроек"""
        if self.language == 'en':
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f'🌐 Language: {"English" if self.language == "en" else "Russian"}',
                        callback_data='change_language'
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=f'📅 Date format: {self.date_format}',
                        callback_data='change_date_format'
                    )
                ],
                [InlineKeyboardButton(text='🔙 Back to Main Menu', callback_data='back_to_main')]
            ])
        else:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f'🌐 Язык: {"Английский" if self.language == "en" else "Русский"}',
                        callback_data='change_language'
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=f'📅 Формат даты: {self.date_format}',
                        callback_data='change_date_format'
                    )
                ],
                [InlineKeyboardButton(text='🔙 В главное меню', callback_data='back_to_main')]
            ])
        return kb

    def get_date_format_keyboard(self) -> InlineKeyboardMarkup:
        """Создает клавиатуру выбора формата даты"""
        if self.language == 'en':
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="DD.MM.YYYY", callback_data="date_format_dd.mm.yyyy")],
                [InlineKeyboardButton(text="YYYY-MM-DD", callback_data="date_format_yyyy-mm-dd")],
                [InlineKeyboardButton(text="MM/DD/YYYY", callback_data="date_format_mm/dd/yyyy")],
                [InlineKeyboardButton(text='🔙 Back', callback_data='back_to_settings')]
            ])
        else:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="ДД.ММ.ГГГГ", callback_data="date_format_dd.mm.yyyy")],
                [InlineKeyboardButton(text="ГГГГ-ММ-ДД", callback_data="date_format_yyyy-mm-dd")],
                [InlineKeyboardButton(text="ММ/ДД/ГГГГ", callback_data="date_format_mm/dd/yyyy")],
                [InlineKeyboardButton(text='🔙 Назад', callback_data='back_to_settings')]
            ])
        return kb

class CalendarKeyboards:
    """Класс для создания клавиатур календаря"""
    @staticmethod
    def get_start_keyboard(language: str = 'ru') -> ReplyKeyboardMarkup:
        """Создает стартовую клавиатуру"""
        if language == 'en':
            kb = ReplyKeyboardMarkup(
                keyboard=[
                    [
                        KeyboardButton(text="📅 Simple Calendar"),
                        KeyboardButton(text="📅 Dialog Calendar")
                    ],
                    [
                        KeyboardButton(text="⚡️ Quick Dates"),
                        KeyboardButton(text="⚙️ Settings")
                    ]
                ],
                resize_keyboard=True
            )
        else:
            kb = ReplyKeyboardMarkup(
                keyboard=[
                    [
                        KeyboardButton(text="📅 Простой календарь"),
                        KeyboardButton(text="📅 Диалоговый календарь")
                    ],
                    [
                        KeyboardButton(text="⚡️ Быстрые даты"),
                        KeyboardButton(text="⚙️ Настройки")
                    ]
                ],
                resize_keyboard=True
            )
        return kb

    @staticmethod
    def get_quick_dates_keyboard(language: str = 'ru') -> ReplyKeyboardMarkup:
        """Создает клавиатуру быстрых дат"""
        if language == 'en':
            kb = ReplyKeyboardMarkup(
                keyboard=[
                    [
                        KeyboardButton(text='📌 Today'),
                        KeyboardButton(text='📌 Tomorrow')
                    ],
                    [
                        KeyboardButton(text='📌 Next Week'),
                        KeyboardButton(text='📌 In 2 Weeks')
                    ],
                    [
                        KeyboardButton(text='📌 Next Month'),
                        KeyboardButton(text='📌 In 3 Months')
                    ],
                    [
                        KeyboardButton(text='📌 Start of Month'),
                        KeyboardButton(text='📌 End of Month')
                    ],
                    [
                        KeyboardButton(text='🔙 Back to Main Menu')
                    ]
                ],
                resize_keyboard=True
            )
        else:
            kb = ReplyKeyboardMarkup(
                keyboard=[
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
                ],
                resize_keyboard=True
            )
        return kb

class QuickDates:
    """Класс для работы с быстрыми датами"""

    @staticmethod
    def get_quick_dates_keyboard(language: str = 'ru') -> ReplyKeyboardMarkup:
        """Создает клавиатуру быстрых дат"""
        if language == 'en':
            kb = ReplyKeyboardMarkup(
                keyboard=[
                    [
                        KeyboardButton(text='📌 Today'),
                        KeyboardButton(text='📌 Tomorrow')
                    ],
                    [
                        KeyboardButton(text='📌 Next Week'),
                        KeyboardButton(text='📌 In 2 Weeks')
                    ],
                    [
                        KeyboardButton(text='📌 Next Month'),
                        KeyboardButton(text='📌 In 3 Months')
                    ],
                    [
                        KeyboardButton(text='📌 Start of Month'),
                        KeyboardButton(text='📌 End of Month')
                    ],
                    [
                        KeyboardButton(text='🔙 Back to Main Menu')
                    ]
                ],
                resize_keyboard=True
            )
        else:
            kb = ReplyKeyboardMarkup(
                keyboard=[
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
                ],
                resize_keyboard=True
            )
        return kb

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
async def cmd_start(message: Message) -> None:
    """
    Conversation's entry point
    """
    try:
        user_id = message.from_user.id
        if user_id not in user_settings:
            user_settings[user_id] = UserSettings()
        
        user_lang = user_settings[user_id].language
        welcome_text = (
            "👋 Welcome to Calendar Bot!\nChoose a calendar type:" if user_lang == 'en'
            else "👋 Добро пожаловать в Календарь Бот!\nВыберите тип календаря:"
        )
        
        await message.answer(
            welcome_text,
            reply_markup=CalendarKeyboards.get_start_keyboard(user_lang)
        )
    except Exception as e:
        logger.error(f"Ошибка в команде /start: {e}")
        error_text = (
            "❌ An error occurred. Please try again later." if user_lang == 'en'
            else "❌ Произошла ошибка. Пожалуйста, попробуйте позже."
        )
        await message.answer(error_text)

@dp.message(Command("help"))
async def command_help_handler(message: Message) -> None:
    """Обработчик команды /help"""
    try:
        user_id = message.from_user.id
        if user_id not in user_settings:
            user_settings[user_id] = UserSettings()
        
        user_lang = user_settings[user_id].language
        
        if user_lang == 'en':
            help_text = (
                "📚 Help for using the bot:\n\n"
                "🔹 /start - Start the bot and show the main menu\n"
                "🔹 /help - Show this help\n"
                "🔹 /settings - Bot settings\n\n"
                "📅 Calendar types:\n"
                "1️⃣ Simple calendar - choose a date in one click\n"
                "2️⃣ Extended calendar - with month navigation\n"
                "3️⃣ Dialog calendar - step-by-step selection\n"
                "4️⃣ Quick dates - popular options\n\n"
                "⚙️ In the settings, you can:\n"
                "- Change the date format\n"
                "- Choose the interface language\n\n"
                "❓ If you have any questions or problems,\n"
                "please contact support"
            )
        else:
            help_text = (
                "📚 Справка по использованию бота:\n\n"
                "🔹 /start - Запустить бота и показать главное меню\n"
                "🔹 /help - Показать эту справку\n"
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
        
        await message.answer(help_text)
    except Exception as e:
        logger.error(f"Ошибка в обработчике /help: {e}")
        await message.answer("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")

@dp.message(Command("settings"))
async def command_settings_handler(message: Message) -> None:
    """Обработчик команды /settings"""
    try:
        user_id = message.from_user.id
        if user_id not in user_settings:
            user_settings[user_id] = UserSettings()
        
        user_lang = user_settings[user_id].language
        
        if user_lang == 'en':
            settings_text = (
                "⚙️ Bot settings\n\n"
                "Choose what you want to set:"
            )
        else:
            settings_text = (
                "⚙️ Настройки бота\n\n"
                "Выберите, что хотите настроить:"
            )
        
        await message.answer(
            settings_text,
            reply_markup=user_settings[user_id].get_settings_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка в обработчике /settings: {e}")
        await message.answer("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")

@dp.message(F.text.in_(["⚙️ Settings", "⚙️ Настройки"]))
async def settings_handler(message: Message) -> None:
    """Обработчик кнопки настроек в главном меню"""
    try:
        user_id = message.from_user.id
        if user_id not in user_settings:
            user_settings[user_id] = UserSettings()
        
        user_lang = user_settings[user_id].language
        settings_text = (
            "⚙️ Bot Settings\n\nChoose what you want to configure:" if user_lang == 'en'
            else "⚙️ Настройки бота\n\nВыберите, что хотите настроить:"
        )
        
        await message.answer(
            settings_text,
            reply_markup=user_settings[user_id].get_settings_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка в обработчике настроек: {e}")
        error_text = (
            "❌ An error occurred. Please try again later." if user_lang == 'en'
            else "❌ Произошла ошибка. Пожалуйста, попробуйте позже."
        )
        await message.answer(error_text)

@dp.message(F.text.in_(["⚡️ Quick Dates", "⚡️ Быстрые даты"]))
async def quick_dates_handler(message: Message) -> None:
    """Обработчик кнопки быстрых дат"""
    try:
        user_id = message.from_user.id
        if user_id not in user_settings:
            user_settings[user_id] = UserSettings()
        
        user_lang = user_settings[user_id].language
        quick_dates_text = (
            "⚡️ Quick Dates\nChoose a date:" if user_lang == 'en'
            else "⚡️ Быстрые даты\nВыберите дату:"
        )
        
        await message.answer(
            quick_dates_text,
            reply_markup=CalendarKeyboards.get_quick_dates_keyboard(user_lang)
        )
    except Exception as e:
        logger.error(f"Ошибка в обработчике быстрых дат: {e}")
        error_text = (
            "❌ An error occurred. Please try again later." if user_lang == 'en'
            else "❌ Произошла ошибка. Пожалуйста, попробуйте позже."
        )
        await message.answer(error_text)

@dp.message(F.text == "📌 Today", F.text == "📌 Сегодня")
async def today_handler(message: Message) -> None:
    """Обработчик выбора сегодняшней даты"""
    try:
        today = datetime.now()
        await message.answer(
            f"✅ Выбрана дата:\n\n{QuickDates.get_date_description(today)}\n\n"
            f"📝 Можете выбрать другую дату или вернуться в главное меню",
            reply_markup=CalendarKeyboards.get_quick_dates_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка в обработчике сегодняшней даты: {e}")
        await message.answer("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")

@dp.message(F.text == "📌 Tomorrow", F.text == "📌 Завтра")
async def tomorrow_handler(message: Message) -> None:
    """Обработчик выбора завтрашней даты"""
    try:
        tomorrow = datetime.now() + datetime.timedelta(days=1)
        await message.answer(
            f"✅ Выбрана дата:\n\n{QuickDates.get_date_description(tomorrow)}\n\n"
            f"📝 Можете выбрать другую дату или вернуться в главное меню",
            reply_markup=CalendarKeyboards.get_quick_dates_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка в обработчике завтрашней даты: {e}")
        await message.answer("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")

@dp.message(F.text == "📌 Next Week", F.text == "📌 Через неделю")
async def next_week_handler(message: Message) -> None:
    """Обработчик выбора даты через неделю"""
    try:
        next_week = datetime.now() + datetime.timedelta(days=7)
        await message.answer(
            f"✅ Выбрана дата:\n\n{QuickDates.get_date_description(next_week)}\n\n"
            f"📝 Можете выбрать другую дату или вернуться в главное меню",
            reply_markup=CalendarKeyboards.get_quick_dates_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка в обработчике даты через неделю: {e}")
        await message.answer("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")

@dp.message(F.text == "📌 In 2 Weeks", F.text == "📌 Через 2 недели")
async def two_weeks_handler(message: Message) -> None:
    """Обработчик выбора даты через 2 недели"""
    try:
        two_weeks = datetime.now() + datetime.timedelta(days=14)
        await message.answer(
            f"✅ Выбрана дата:\n\n{QuickDates.get_date_description(two_weeks)}\n\n"
            f"📝 Можете выбрать другую дату или вернуться в главное меню",
            reply_markup=CalendarKeyboards.get_quick_dates_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка в обработчике даты через 2 недели: {e}")
        await message.answer("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")

@dp.message(F.text == "📌 Next Month", F.text == "📌 Через месяц")
async def next_month_handler(message: Message) -> None:
    """Обработчик выбора даты через месяц"""
    try:
        next_month = datetime.now() + datetime.timedelta(days=30)
        await message.answer(
            f"✅ Выбрана дата:\n\n{QuickDates.get_date_description(next_month)}\n\n"
            f"📝 Можете выбрать другую дату или вернуться в главное меню",
            reply_markup=CalendarKeyboards.get_quick_dates_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка в обработчике даты через месяц: {e}")
        await message.answer("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")

@dp.message(F.text == "📌 In 3 Months", F.text == "📌 Через 3 месяца")
async def three_months_handler(message: Message) -> None:
    """Обработчик выбора даты через 3 месяца"""
    try:
        three_months = datetime.now() + datetime.timedelta(days=90)
        await message.answer(
            f"✅ Выбрана дата:\n\n{QuickDates.get_date_description(three_months)}\n\n"
            f"📝 Можете выбрать другую дату или вернуться в главное меню",
            reply_markup=CalendarKeyboards.get_quick_dates_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка в обработчике даты через 3 месяца: {e}")
        await message.answer("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")

@dp.message(F.text == "📌 Start of Month", F.text == "📌 Начало месяца")
async def start_of_month_handler(message: Message) -> None:
    """Обработчик выбора начала текущего месяца"""
    try:
        today = datetime.now()
        start_of_month = today.replace(day=1)
        await message.answer(
            f"✅ Выбрана дата:\n\n{QuickDates.get_date_description(start_of_month)}\n\n"
            f"📝 Можете выбрать другую дату или вернуться в главное меню",
            reply_markup=CalendarKeyboards.get_quick_dates_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка в обработчике начала месяца: {e}")
        await message.answer("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")

@dp.message(F.text == "📌 End of Month", F.text == "📌 Конец месяца")
async def end_of_month_handler(message: Message) -> None:
    """Обработчик выбора конца текущего месяца"""
    try:
        today = datetime.now()
        # Получаем последний день текущего месяца
        if today.month == 12:
            last_day = today.replace(day=31)
        else:
            last_day = today.replace(month=today.month + 1, day=1) - datetime.timedelta(days=1)
        
        await message.answer(
            f"✅ Выбрана дата:\n\n{QuickDates.get_date_description(last_day)}\n\n"
            f"📝 Можете выбрать другую дату или вернуться в главное меню",
            reply_markup=CalendarKeyboards.get_quick_dates_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка в обработчике конца месяца: {e}")
        await message.answer("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")

@dp.message(F.text.in_(["🔙 Back to Main Menu", "🔙 Вернуться в главное меню"]))
async def back_to_main_menu(message: Message) -> None:
    """Обработчик возврата в главное меню"""
    try:
        user_id = message.from_user.id
        if user_id not in user_settings:
            user_settings[user_id] = UserSettings()
        
        user_lang = user_settings[user_id].language
        main_menu_text = (
            "🏠 Main Menu\nChoose a calendar type:" if user_lang == 'en'
            else "🏠 Главное меню\nВыберите тип календаря:"
        )
        
        await message.answer(
            main_menu_text,
            reply_markup=CalendarKeyboards.get_start_keyboard(user_lang)
        )
    except Exception as e:
        logger.error(f"Ошибка при возврате в главное меню: {e}")
        error_text = (
            "❌ An error occurred. Please try again later." if user_lang == 'en'
            else "❌ Произошла ошибка. Пожалуйста, попробуйте позже."
        )
        await message.answer(error_text)

@dp.callback_query(F.data == "change_language")
async def change_language_handler(callback_query: CallbackQuery):
    """Обработчик кнопки изменения языка"""
    try:
        user_id = callback_query.from_user.id
        if user_id not in user_settings:
            user_settings[user_id] = UserSettings()
        
        user_lang = user_settings[user_id].language
        language_text = (
            "Select language:" if user_lang == 'en'
            else "Выберите язык:"
        )
        
        await callback_query.message.edit_text(
            language_text,
            reply_markup=UserSettings.get_language_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка при открытии меню выбора языка: {e}")
        error_text = (
            "❌ An error occurred. Please try again later." if user_lang == 'en'
            else "❌ Произошла ошибка. Пожалуйста, попробуйте позже."
        )
        await callback_query.message.answer(error_text)

@dp.callback_query(F.data.startswith("lang_"))
async def process_language_selection(callback_query: CallbackQuery):
    """Обработчик выбора языка"""
    try:
        user_id = callback_query.from_user.id
        new_lang = callback_query.data.split('_')[1]
        
        if user_id not in user_settings:
            user_settings[user_id] = UserSettings()
        
        old_lang = user_settings[user_id].language
        user_settings[user_id].language = new_lang
        
        # Определяем текст в зависимости от нового языка
        success_text = (
            "✅ Language changed successfully!" if new_lang == 'en'
            else "✅ Язык успешно изменен!"
        )
        
        # Обновляем сообщение с настройками
        await callback_query.message.edit_text(
            success_text,
            reply_markup=user_settings[user_id].get_settings_keyboard()
        )
        
        # Отправляем новое главное меню с обновленным языком
        main_menu_text = (
            "🏠 Main Menu\nChoose a calendar type:" if new_lang == 'en'
            else "🏠 Главное меню\nВыберите тип календаря:"
        )
        
        # Отправляем новую клавиатуру с правильным языком
        await callback_query.message.answer(
            main_menu_text,
            reply_markup=CalendarKeyboards.get_start_keyboard(new_lang)
        )
        
    except Exception as e:
        logger.error(f"Ошибка при смене языка: {e}")
        error_text = (
            "❌ An error occurred. Please try again later." if new_lang == 'en'
            else "❌ Произошла ошибка. Пожалуйста, попробуйте позже."
        )
        await callback_query.message.answer(error_text)

@dp.callback_query(F.data == "change_date_format")
async def change_date_format_handler(callback_query: CallbackQuery):
    """Обработчик кнопки изменения формата даты"""
    try:
        user_id = callback_query.from_user.id
        if user_id not in user_settings:
            user_settings[user_id] = UserSettings()
        
        user_lang = user_settings[user_id].language
        format_text = (
            "Select date format:" if user_lang == 'en'
            else "Выберите формат даты:"
        )
        
        await callback_query.message.edit_text(
            format_text,
            reply_markup=user_settings[user_id].get_date_format_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка при открытии меню формата даты: {e}")
        error_text = (
            "❌ An error occurred. Please try again later." if user_lang == 'en'
            else "❌ Произошла ошибка. Пожалуйста, попробуйте позже."
        )
        await callback_query.message.answer(error_text)

@dp.callback_query(F.data.startswith("date_format_"))
async def process_date_format_selection(callback_query: CallbackQuery):
    """Обработчик выбора формата даты"""
    try:
        user_id = callback_query.from_user.id
        if user_id not in user_settings:
            user_settings[user_id] = UserSettings()
        
        new_format = callback_query.data.replace("date_format_", "")
        user_settings[user_id].date_format = new_format
        
        user_lang = user_settings[user_id].language
        success_text = (
            "✅ Date format changed successfully!" if user_lang == 'en'
            else "✅ Формат даты успешно изменен!"
        )
        
        await callback_query.message.edit_text(
            success_text,
            reply_markup=user_settings[user_id].get_settings_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка при выборе формата даты: {e}")
        error_text = (
            "❌ An error occurred. Please try again later." if user_lang == 'en'
            else "❌ Произошла ошибка. Пожалуйста, попробуйте позже."
        )
        await callback_query.message.answer(error_text)

@dp.callback_query(F.data == "back_to_main")
async def process_back_to_main(callback_query: CallbackQuery):
    """Обработчик возврата в главное меню из настроек"""
    try:
        user_id = callback_query.from_user.id
        if user_id not in user_settings:
            user_settings[user_id] = UserSettings()
        
        user_lang = user_settings[user_id].language
        main_menu_text = (
            "🏠 Main Menu\nChoose a calendar type:" if user_lang == 'en'
            else "🏠 Главное меню\nВыберите тип календаря:"
        )
        
        await callback_query.message.answer(
            main_menu_text,
            reply_markup=CalendarKeyboards.get_start_keyboard(user_lang)
        )
        await callback_query.message.delete()
    except Exception as e:
        logger.error(f"Ошибка при возврате в главное меню: {e}")
        error_text = (
            "❌ An error occurred. Please try again later." if user_lang == 'en'
            else "❌ Произошла ошибка. Пожалуйста, попробуйте позже."
        )
        await callback_query.message.answer(error_text)

@dp.callback_query(F.data == "back_to_settings")
async def process_back_to_settings(callback_query: CallbackQuery):
    """Обработчик возврата в меню настроек"""
    try:
        user_id = callback_query.from_user.id
        if user_id not in user_settings:
            user_settings[user_id] = UserSettings()
        
        user_lang = user_settings[user_id].language
        settings_text = (
            "⚙️ Bot Settings\n\nChoose what you want to configure:" if user_lang == 'en'
            else "⚙️ Настройки бота\n\nВыберите, что хотите настроить:"
        )
        
        await callback_query.message.edit_text(
            settings_text,
            reply_markup=user_settings[user_id].get_settings_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка при возврате в настройки: {e}")
        error_text = (
            "❌ An error occurred. Please try again later." if user_lang == 'en'
            else "❌ Произошла ошибка. Пожалуйста, попробуйте позже."
        )
        await callback_query.message.answer(error_text)

@dp.message(F.text.in_(["📅 Simple Calendar", "📅 Простой календарь"]))
async def nav_cal_handler(message: Message) -> None:
    """Обработчик простого календаря"""
    try:
        user_id = message.from_user.id
        if user_id not in user_settings:
            user_settings[user_id] = UserSettings()
        
        user_lang = user_settings[user_id].language
        calendar_text = (
            "📅 Simple Calendar\nSelect a date:" if user_lang == 'en'
            else "📅 Простой календарь\nВыберите дату:"
        )
        
        # Создаем календарь с указанным языком и кнопками
        calendar = SimpleCalendar(
            locale=user_lang,
            show_alerts=True
        )
        await message.answer(
            calendar_text,
            reply_markup=await calendar.start_calendar()
        )
    except Exception as e:
        logger.error(f"Ошибка в обработчике простого календаря: {e}")
        error_text = (
            "❌ An error occurred. Please try again later." if user_lang == 'en'
            else "❌ Произошла ошибка. Пожалуйста, попробуйте позже."
        )
        await message.answer(error_text)

@dp.message(F.text.in_(["📅 Dialog Calendar", "📅 Диалоговый календарь"]))
async def dialog_cal_handler(message: Message) -> None:
    """Обработчик диалогового календаря"""
    try:
        user_id = message.from_user.id
        if user_id not in user_settings:
            user_settings[user_id] = UserSettings()
        
        user_lang = user_settings[user_id].language
        calendar_text = (
            "📅 Dialog Calendar\nSelect a year:" if user_lang == 'en'
            else "📅 Диалоговый календарь\nВыберите год:"
        )
        
        # Создаем календарь с указанным языком и кнопками
        calendar = DialogCalendar(
            locale=user_lang,
            show_alerts=True
        )
        await message.answer(
            calendar_text,
            reply_markup=await calendar.start_calendar()
        )
    except Exception as e:
        logger.error(f"Ошибка в обработчике диалогового календаря: {e}")
        error_text = (
            "❌ An error occurred. Please try again later." if user_lang == 'en'
            else "❌ Произошла ошибка. Пожалуйста, попробуйте позже."
        )
        await message.answer(error_text)

@dp.callback_query(SimpleCalendarCallback.filter())
async def process_simple_calendar(callback_query: CallbackQuery, callback_data: dict):
    """Обработчик простого календаря"""
    try:
        user_id = callback_query.from_user.id
        if user_id not in user_settings:
            user_settings[user_id] = UserSettings()
        
        user_lang = user_settings[user_id].language
        # Создаем календарь с указанным языком и кнопками
        calendar = SimpleCalendar(
            locale=user_lang,
            show_alerts=True
        )
        selected, date = await calendar.process_selection(callback_query, callback_data)
        
        if selected:
            date_format = user_settings[user_id].date_format
            formatted_date = date.strftime(DATE_FORMATS[date_format])
            success_text = (
                f"✅ You selected: {formatted_date}" if user_lang == 'en'
                else f"✅ Вы выбрали: {formatted_date}"
            )
            await callback_query.message.answer(success_text)
    except Exception as e:
        logger.error(f"Ошибка в обработчике выбора даты (простой календарь): {e}")
        error_text = (
            "❌ An error occurred. Please try again later." if user_lang == 'en'
            else "❌ Произошла ошибка. Пожалуйста, попробуйте позже."
        )
        await callback_query.message.answer(error_text)

@dp.callback_query(DialogCalendarCallback.filter())
async def process_dialog_calendar(callback_query: CallbackQuery, callback_data: dict):
    """Обработчик диалогового календаря"""
    try:
        user_id = callback_query.from_user.id
        if user_id not in user_settings:
            user_settings[user_id] = UserSettings()
        
        user_lang = user_settings[user_id].language
        # Создаем календарь с указанным языком и кнопками
        calendar = DialogCalendar(
            locale=user_lang,
            show_alerts=True
        )
        selected, date = await calendar.process_selection(callback_query, callback_data)
        
        if selected:
            date_format = user_settings[user_id].date_format
            formatted_date = date.strftime(DATE_FORMATS[date_format])
            success_text = (
                f"✅ You selected: {formatted_date}" if user_lang == 'en'
                else f"✅ Вы выбрали: {formatted_date}"
            )
            await callback_query.message.answer(success_text)
    except Exception as e:
        logger.error(f"Ошибка в обработчике выбора даты (диалоговый календарь): {e}")
        error_text = (
            "❌ An error occurred. Please try again later." if user_lang == 'en'
            else "❌ Произошла ошибка. Пожалуйста, попробуйте позже."
        )
        await callback_query.message.answer(error_text)

async def main() -> None:
    """
    Основная функция запуска бота
    """
    try:
        # Запуск процесса обработки событий
        await dp.start_polling(bot)
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске бота: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
