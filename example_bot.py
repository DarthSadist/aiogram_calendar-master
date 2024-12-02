import logging
import asyncio
import sys
from datetime import datetime

import locale
locale.setlocale(locale.LC_ALL, 'ru_RU.utf8')

from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback, DialogCalendar, DialogCalendarCallback, \
    get_user_locale
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.filters.callback_data import CallbackData
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, CallbackQuery
from aiogram.utils.markdown import hbold
from aiogram.client.default import DefaultBotProperties

from bot_config import API_TOKEN

# API_TOKEN = '' uncomment and insert your telegram bot API key here

# All handlers should be attached to the Router (or Dispatcher)
dp = Dispatcher()


# initialising keyboard, each button will be used to start a calendar with different initial settings
kb = [
    [   # Кнопки для навигационного календаря
        KeyboardButton(text='Обычный календарь'),
        KeyboardButton(text='Календарь с выбором месяца'),
    ],
    [   # Кнопки для диалогового календаря
        KeyboardButton(text='Диалоговый календарь'),
        KeyboardButton(text='Диалоговый календарь с годом'),
    ],
    [
        KeyboardButton(text='Диалоговый календарь с месяцем')
    ]
]
start_kb = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


# when user sends `/start` command, answering with inline calendar
@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    Этот обработчик получает сообщения с командой `/start`
    """
    await message.answer(
        f"Привет, {hbold(message.from_user.full_name)}!\n"
        f"Это демонстрация календаря для aiogram.\n"
        f"Выберите тип календаря:",
        reply_markup=start_kb
    )


# стандартный способ отображения календаря - дата установлена на сегодня
@dp.message(F.text == "Обычный календарь")
async def nav_cal_handler(message: Message):
    await message.answer(
        "Выберите дату: ",
        reply_markup=await SimpleCalendar().start_calendar()
    )


# можно запустить с определенного года и месяца с разрешенным диапазоном дат
@dp.message(F.text == "Календарь с выбором месяца")
async def nav_cal_handler_date(message: Message):
    calendar = SimpleCalendar()
    calendar.set_dates_range(datetime(2022, 1, 1), datetime(2025, 12, 31))
    await message.answer(
        "Календарь открыт на февраль 2024. Выберите дату: ",
        reply_markup=await calendar.start_calendar(year=2024, month=2)
    )


# обработка простого календаря - фильтрация обратных вызовов календаря
@dp.callback_query(SimpleCalendarCallback.filter())
async def process_simple_calendar(callback_query: CallbackQuery, callback_data: CallbackData):
    calendar = SimpleCalendar(
        show_alerts=True,  # показывать всплывающие окна при ошибках
    )
    calendar.set_dates_range(datetime(2022, 1, 1), datetime(2025, 12, 31))

    selected, date = await calendar.process_selection(callback_query, callback_data)
    if selected:
        await callback_query.message.answer(
            f'Вы выбрали: {date.strftime("%d.%m.%Y")}'
        )


# диалоговый календарь
@dp.message(F.text == "Диалоговый календарь")
async def dialog_cal_handler(message: Message):
    await message.answer(
        "Выберите дату: ",
        reply_markup=await DialogCalendar().start_calendar()
    )


# запуск календаря с 1989 года
@dp.message(F.text == "Диалоговый календарь с годом")
async def dialog_cal_handler_year(message: Message):
    await message.answer(
        "Выберите дату (начиная с 1989 года): ",
        reply_markup=await DialogCalendar().start_calendar(year=1989)
    )


# запуск диалогового календаря с 1989 года и месяца
@dp.message(F.text == "Диалоговый календарь с месяцем")
async def dialog_cal_handler_month(message: Message):
    await message.answer(
        "Выберите дату (начиная с июня 1989): ",
        reply_markup=await DialogCalendar().start_calendar(year=1989, month=6)
    )


# обработка диалогового календаря
@dp.callback_query(DialogCalendarCallback.filter())
async def process_dialog_calendar(callback_query: CallbackQuery, callback_data: CallbackData):
    selected, date = await DialogCalendar().process_selection(callback_query, callback_data)
    if selected:
        await callback_query.message.answer(
            f'Вы выбрали: {date.strftime("%d.%m.%Y")}'
        )


async def main() -> None:
    # Initialize Bot instance with a default parse mode which will be passed to all API calls
    bot = Bot(API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
