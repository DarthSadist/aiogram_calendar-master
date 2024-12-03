from typing import Dict, Optional

class Localization:
    """Class for managing calendar localizations"""
    
    # Default translations
    TRANSLATIONS = {
        'ru': {
            'months': [
                'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
            ],
            'days': ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'],
            'select_year': 'Выберите год',
            'select_month': 'Выберите месяц',
            'select_day': 'Выберите день',
            'previous_month': '<<',
            'next_month': '>>',
            'ignore': 'Игнорировать',
            'today': 'Сегодня',
            'tomorrow': 'Завтра',
            'next_week': 'Через неделю',
            'two_weeks': 'Через 2 недели',
            'next_month': 'Через месяц',
            'three_months': 'Через 3 месяца',
            'start_month': 'Начало месяца',
            'end_month': 'Конец месяца',
            'back': 'Назад',
            'settings': 'Настройки',
            'language': 'Язык',
            'date_format': 'Формат даты'
        },
        'en': {
            'months': [
                'January', 'February', 'March', 'April', 'May', 'June',
                'July', 'August', 'September', 'October', 'November', 'December'
            ],
            'days': ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'],
            'select_year': 'Select year',
            'select_month': 'Select month',
            'select_day': 'Select day',
            'previous_month': '<<',
            'next_month': '>>',
            'ignore': 'Ignore',
            'today': 'Today',
            'tomorrow': 'Tomorrow',
            'next_week': 'Next week',
            'two_weeks': 'In 2 weeks',
            'next_month': 'Next month',
            'three_months': 'In 3 months',
            'start_month': 'Start of month',
            'end_month': 'End of month',
            'back': 'Back',
            'settings': 'Settings',
            'language': 'Language',
            'date_format': 'Date format'
        }
    }

    def __init__(self, language: str = 'en'):
        """
        Initialize localization
        
        Args:
            language (str): Language code ('en' or 'ru')
        """
        self.language = language if language in self.TRANSLATIONS else 'en'

    def get_text(self, key: str) -> str:
        """
        Get localized text by key
        
        Args:
            key (str): Translation key
            
        Returns:
            str: Localized text
        """
        return self.TRANSLATIONS[self.language].get(key, key)

    def get_month_name(self, month: int) -> str:
        """
        Get localized month name
        
        Args:
            month (int): Month number (1-12)
            
        Returns:
            str: Localized month name
        """
        if 1 <= month <= 12:
            return self.TRANSLATIONS[self.language]['months'][month - 1]
        return str(month)

    def get_weekday_name(self, weekday: int) -> str:
        """
        Get localized weekday name
        
        Args:
            weekday (int): Weekday number (0-6, where 0 is Monday)
            
        Returns:
            str: Localized weekday name
        """
        if 0 <= weekday <= 6:
            return self.TRANSLATIONS[self.language]['days'][weekday]
        return str(weekday)

    @classmethod
    def get_available_languages(cls) -> list:
        """
        Get list of available languages
        
        Returns:
            list: List of available language codes
        """
        return list(cls.TRANSLATIONS.keys())
