"""
Конфигурация для парсера вакансий rabota.by
"""

import os


class Config:
    """Класс конфигурации проекта"""

    def __init__(self):
        # Пути к директориям
        self.BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.DATA_DIR = os.path.join(self.BASE_DIR, 'data')
        self.CONFIG_DIR = os.path.join(self.BASE_DIR, 'config')

        # Создаем директории если их нет
        os.makedirs(self.DATA_DIR, exist_ok=True)
        os.makedirs(self.CONFIG_DIR, exist_ok=True)

        # Файлы с источниками
        self.LINKS_FILE = os.path.join(self.CONFIG_DIR, 'search_links.txt')
        self.NAMES_FILE = os.path.join(self.CONFIG_DIR, 'specializations.txt')

        # Настройки парсера
        self.PARSER_CONFIG = {
            'delay_between_requests': 0.1,  # Задержка между запросами (секунды)
            'delay_between_pages': 0.2,  # Задержка между страницами
            'max_retries': 3,  # Максимальное количество попыток
            'timeout': 30,  # Таймаут для загрузки страницы
            'headless': False,  # Headless режим браузера
            'chrome_version': 144,  # Версия Chrome (None = автоопределение)
        }

        # Настройки Chrome
        self.CHROME_OPTIONS = [
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--window-size=1920,1080',
        ]

        # Если нужен headless режим
        if self.PARSER_CONFIG['headless']:
            self.CHROME_OPTIONS.append('--headless=new')

    def get_data_file(self, filename: str) -> str:
        """Возвращает полный путь к файлу данных"""
        return os.path.join(self.DATA_DIR, filename)
