"""
Модуль для обработки и гармонизации данных о вакансиях
"""

import json
from typing import List, Dict
from src import harmonization as harm


class DataProcessor:
    """Класс для обработки и гармонизации данных о вакансиях"""

    def __init__(self, config):
        self.config = config

    def process_vacancies(self, vacancies: List[Dict], links_data: List[Dict[str, str]]) -> List[Dict]:
        """
        Обрабатывает и гармонизирует данные о вакансиях

        Args:
            vacancies: Список собранных вакансий
            links_data: Список со ссылками и специализациями

        Returns:
            List[Dict]: Обработанные и гармонизированные вакансии
        """
        # Создаем словарь для быстрого поиска специализаций
        links_dict = {item['url']: item['specialization'] for item in links_data}

        processed = []

        for vacancy in vacancies:
            # Добавляем специализацию
            url = vacancy.get('url', '')
            specialization = links_dict.get(url, 'Не указано')
            vacancy['specialization'] = specialization

            # Гармонизация данных
            processed_vacancy = self._harmonize_vacancy(vacancy)

            # Обогащение данных
            enriched_vacancy = self._enrich_vacancy(processed_vacancy)

            processed.append(enriched_vacancy)

        return processed

    def _harmonize_vacancy(self, vacancy: Dict) -> Dict:
        """
        Применяет гармонизацию к отдельной вакансии

        Args:
            vacancy: Данные о вакансии

        Returns:
            Dict: Гармонизированная вакансия
        """
        # Гармонизация разряда специалиста
        vacancy['specialist_level'] = harm.harmonize_specialist_level(
            vacancy.get('title', '')
        )

        # Гармонизация опыта работы
        vacancy['experience_harmonized'] = harm.harmonize_experience(
            vacancy.get('experience', '')
        )

        # Гармонизация типа занятости
        vacancy['employment_type'] = harm.harmonize_employment_type(
            vacancy.get('work_schedule', '')
        )

        # Извлечение и гармонизация зарплаты
        salary_info = harm.extract_salary_range(vacancy.get('salary_raw', ''))
        vacancy['salary_min'] = salary_info['min']
        vacancy['salary_max'] = salary_info['max']
        vacancy['currency'] = salary_info['currency']
        vacancy['salary_type'] = salary_info['type']
        vacancy['salary_avg'] = harm.get_average_salary(
            salary_info['min'], salary_info['max']
        )

        # Гармонизация города
        vacancy['city'] = harm.harmonize_city(vacancy.get('address', ''))

        # Классификация специализации
        vacancy['specialization_category'] = harm.classify_specialization_category(
            vacancy.get('specialization', '')
        )

        return vacancy

    def _enrich_vacancy(self, vacancy: Dict) -> Dict:
        """
        Обогащает вакансию дополнительными полями

        Args:
            vacancy: Гармонизированная вакансия

        Returns:
            Dict: Обогащенная вакансия
        """
        # Комбинированное поле company_vacancy
        company = vacancy.get('company', 'Не указано')
        title = vacancy.get('title', 'Не указано')
        vacancy['company_vacancy'] = f"{company} --- {title}"

        # Флаги для удобной фильтрации
        vacancy['has_salary'] = vacancy['salary_min'] is not None
        vacancy['remote_work'] = 'удален' in vacancy.get('work_format', '').lower()

        # Длина описания (для анализа качества вакансий)
        description = vacancy.get('description', '')
        vacancy['description_length'] = len(description) if description != 'Не указано' else 0

        # Количество навыков
        skills = vacancy.get('skills', '')
        if skills and skills != 'Не указано':
            vacancy['skills_count'] = len(skills.split(';'))
        else:
            vacancy['skills_count'] = 0

        return vacancy

    def process_single_vacancy(self, vacancy: Dict, links_dict: Dict[str, str]) -> Dict:
        """
        Обрабатывает и гармонизирует одну вакансию

        Args:
            vacancy: Сырые данные вакансии
            links_dict: Словарь {url: специализация}

        Returns:
            Dict: Обработанная вакансия
        """
        url = vacancy.get('url', '')
        vacancy['specialization'] = links_dict.get(url, 'Не указано')
        processed = self._harmonize_vacancy(vacancy)
        return self._enrich_vacancy(processed)

    def save_final_data(self, processed_data: List[Dict], date_str: str):
        """
        Сохраняет финальные обработанные данные

        Args:
            processed_data: Обработанные вакансии
            date_str: Дата в формате MM.YYYY
        """
        output_file = self.config.get_data_file(f'data_finally_{date_str}_Rabota_by.json')

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(processed_data, f, indent=4, ensure_ascii=False)

        print(f"   💾 Финальные данные сохранены: {output_file}")

    def generate_statistics(self, processed_data: List[Dict]) -> Dict:
        """
        Генерирует статистику по вакансиям

        Args:
            processed_data: Обработанные вакансии

        Returns:
            Dict: Статистика
        """
        stats = {
            'total_vacancies': len(processed_data),
            'with_salary': sum(1 for v in processed_data if v['has_salary']),
            'remote_work': sum(1 for v in processed_data if v['remote_work']),
            'by_level': {},
            'by_city': {},
            'by_category': {},
        }

        # Подсчет по разрядам
        for vacancy in processed_data:
            level = vacancy.get('specialist_level', 'Не указано')
            stats['by_level'][level] = stats['by_level'].get(level, 0) + 1

            city = vacancy.get('city', 'Не указано')
            stats['by_city'][city] = stats['by_city'].get(city, 0) + 1

            category = vacancy.get('specialization_category', 'Другое')
            stats['by_category'][category] = stats['by_category'].get(category, 0) + 1

        return stats
