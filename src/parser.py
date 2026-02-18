"""
Модуль для парсинга вакансий с сайта rabota.by
"""

import os
import time
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional
import json


class VacancyParser:
    """Класс для парсинга вакансий с rabota.by"""

    def __init__(self, config):
        self.config = config
        self.driver = None

    def _init_driver(self):
        """Инициализация Chrome драйвера"""
        if self.driver is None:
            max_attempts = 3
            last_error = None

            # Получаем версию Chrome из конфига
            chrome_version = self.config.PARSER_CONFIG.get('chrome_version', None)

            for attempt in range(1, max_attempts + 1):
                try:
                    
                    # Инициализируем драйвер БЕЗ опций (undetected-chromedriver сам все настроит)
                    if chrome_version:
                        self.driver = uc.Chrome(version_main=chrome_version)
                    else:
                        self.driver = uc.Chrome()
                    return

                except Exception as e:
                    last_error = e
                    if attempt < max_attempts:
                        time.sleep(3)

            # Если все попытки неудачны
            raise Exception(f"Не удалось инициализировать Chrome драйвер после {max_attempts} попыток. Последняя ошибка: {last_error}")

    def _close_driver(self):
        """Закрытие Chrome драйвера"""
        if self.driver:
            try:
                self.driver.quit()
                print("[OK] Chrome драйвер закрыт")
            except Exception as e:
                print(f"[!] Предупреждение при закрытии драйвера: {str(e)[:50]}")
            finally:
                self.driver = None
                time.sleep(0.5)  # Даем время на очистку процессов

    def collect_vacancy_links(self) -> List[Dict[str, str]]:
        """
        Собирает ссылки на все вакансии по заданным специализациям

        Возвращает:
            List[Dict]: Список словарей {'Специализация': str, 'Ссылка': str}
        """
        links_data = []

        # Загружаем ссылки на поиск и названия специализаций
        with open(self.config.LINKS_FILE, encoding='utf-8') as f:
            search_links = [
                line.strip() for line in f.readlines()
                if line.strip() and not line.strip().startswith('#')
            ]

        with open(self.config.NAMES_FILE, encoding='utf-8') as f:
            specializations = [
                line.strip() for line in f.readlines()
                if line.strip() and not line.strip().startswith('#')
            ]

        total_specs = len(specializations)

        for idx, (search_link, spec_name) in enumerate(zip(search_links, specializations), 1):
            print(f"   [+] Обработка специализации {idx}/{total_specs}: {spec_name}")

            # Открываем страницу поиска
            self.driver.get(search_link)
            time.sleep(self.config.PARSER_CONFIG['delay_between_pages'])

            content = self.driver.page_source
            soup = BeautifulSoup(content, 'lxml')

            # Определяем количество страниц
            try:
                pager_links = soup.find_all('a', {'data-qa': 'pager-page'})
                pages_count = int(pager_links[-1].text) if pager_links else 1
            except:
                pages_count = 1

            # Собираем ссылки со всех страниц
            for page_num in range(pages_count):
                page_url = f'{search_link}&page={page_num}'
                self.driver.get(page_url)
                time.sleep(self.config.PARSER_CONFIG['delay_between_requests'])

                content = self.driver.page_source
                soup = BeautifulSoup(content, 'lxml')

                # Извлекаем ссылки на вакансии
                try:
                    results_div = soup.find('div', {'data-qa': 'vacancy-serp__results'})
                    vacancy_links = results_div.find_all('a', {'data-qa': 'serp-item__title'})

                    for link in vacancy_links:
                        vacancy_url = link.get('href')
                        if vacancy_url:
                            links_data.append({
                                'specialization': spec_name,
                                'url': vacancy_url
                            })
                except Exception as e:
                    print(f"      [!] Ошибка на странице {page_num + 1}: {str(e)[:50]}")

            print(f"      [OK] Собрано ссылок: {sum(1 for x in links_data if x['specialization'] == spec_name)}")

        return links_data

    def parse_vacancy_page(self, url: str) -> Optional[Dict]:
        """
        Парсит одну страницу вакансии

        Args:
            url: URL вакансии

        Returns:
            Dict: Данные о вакансии или None при ошибке
        """
        try:
            self.driver.get(url)
            time.sleep(self.config.PARSER_CONFIG['delay_between_requests'])

            content = self.driver.page_source
            soup = BeautifulSoup(content, 'lxml')

            cur_date = datetime.now().strftime("%d.%m.%Y")
            cur_time = datetime.now().strftime("%H:%M")

            # Извлечение данных
            data = {
                "title": self._extract_title(soup),
                "salary_raw": self._extract_salary(soup),
                "experience": self._extract_experience(soup),
                "work_schedule": self._extract_employment(soup),
                "work_format": self._extract_work_format(soup),
                "company": self._extract_company(soup),
                "address": self._extract_address(soup),
                "description": self._extract_description(soup),
                "skills": self._extract_skills(soup),
                "url": url,
                "monitoring_date": cur_date,
                "monitoring_time": cur_time
            }

            return data

        except Exception as e:
            print(f"      [!] Ошибка парсинга {url[:50]}...: {str(e)[:50]}")
            return None

    def _extract_title(self, soup) -> str:
        """Извлекает название вакансии"""
        try:
            return soup.find("h1").text.strip()
        except:
            return "Не указано"

    def _extract_salary(self, soup) -> str:
        """
        Извлекает зарплату.
        Поддерживает BYN (Br), USD ($), EUR (€), RUB (₽).
        Обрабатывает случаи: диапазон, только от, только до, не указано.
        """
        try:
            # Ищем основной блок зарплаты (любой тег: div, p, span и т.д.)
            salary_elem = soup.find(attrs={'data-qa': 'vacancy-salary'})
            if salary_elem:
                text = salary_elem.get_text(separator=' ')
                text = ' '.join(text.split())  # нормализуем пробелы
                if text:
                    return text

            # Запасной вариант — только спан с типом выплаты
            salary_elem = soup.find(attrs={'data-qa': 'vacancy-salary-compensation-type-net'})
            if salary_elem:
                text = salary_elem.get_text(separator=' ')
                text = ' '.join(text.split())
                if text:
                    return text

            return "Уровень дохода не указан"
        except:
            return "Уровень дохода не указан"

    def _extract_experience(self, soup) -> str:
        """Извлекает требуемый опыт работы"""
        try:
            return soup.find("span", {"data-qa": 'vacancy-experience'}).text
        except:
            return "Не указано"

    def _extract_employment(self, soup) -> str:
        """Извлекает тип занятости"""
        try:
            return soup.find("div", class_='dotted-wrapper--xVk7Cm8wgsAU4cbP').text
        except:
            return "Не указано"

    def _extract_company(self, soup) -> str:
        """Извлекает название компании"""
        try:
            return soup.find("span", class_='vacancy-company-name').text
        except:
            return "Не указано"

    def _extract_address(self, soup) -> str:
        """Извлекает адрес"""
        try:
            return soup.find("span", {"data-qa": "vacancy-view-raw-address"}).text
        except:
            return "Не указано"

    def _extract_description(self, soup) -> str:
        """Извлекает описание вакансии"""
        try:
            desc = soup.find("div", class_='tmpl_hh_wrapper')
            if desc:
                return desc.text.strip()

            desc = soup.find("div", class_='g-user-content')
            if desc:
                return desc.text.strip()

            return "Не указано"
        except:
            return "Не указано"

    def _extract_work_format(self, soup) -> str:
        """Извлекает формат работы (офис, гибрид, удалённая и т.д.)"""
        try:
            elem = soup.find("p", {"data-qa": "work-formats-text"})
            if elem:
                return elem.get_text(separator=', ').strip()
            return "Не указано"
        except:
            return "Не указано"

    def _extract_skills(self, soup) -> str:
        """Извлекает навыки"""
        try:
            skills_elements = soup.find_all('li', {'data-qa': 'skills-element'})
            skills = []
            for skill_elem in skills_elements:
                skill = skill_elem.find('div').text
                skills.append(skill)

            return '; '.join(skills) if skills else "Не указано"
        except:
            return "Не указано"

    def parse_vacancies(self, links_data: List[Dict[str, str]]) -> List[Dict]:
        """
        Парсит все вакансии из списка ссылок

        Args:
            links_data: Список словарей со ссылками и специализациями

        Returns:
            List[Dict]: Список данных о вакансиях
        """
        self._init_driver()
        vacancies = []
        failed_links = []

        try:
            total = len(links_data)

            for idx, link_info in enumerate(links_data, 1):
                url = link_info['url']

                if idx % 10 == 0 or idx == total:
                    print(f"   [+] Обработано: {idx}/{total} вакансий")

                vacancy_data = self.parse_vacancy_page(url)

                if vacancy_data:
                    vacancies.append(vacancy_data)
                else:
                    failed_links.append(url)

            if failed_links:
                print(f"\n   [!] Не удалось спарсить {len(failed_links)} вакансий")

        finally:
            self._close_driver()

        return vacancies

    def save_links(self, links_data: List[Dict[str, str]], date_str: str):
        """Сохраняет ссылки в файлы, добавляя только новые (дедупликация по URL)"""
        json_file = self.config.get_data_file(f'links_and_names_{date_str}_rabota_by.json')
        txt_file = self.config.get_data_file(f'url_list_{date_str}_RabotaBy.txt')

        # Загружаем уже существующие ссылки из JSON (если файл есть)
        existing_links = []
        if os.path.exists(json_file):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    existing_links = json.load(f)
            except (json.JSONDecodeError, IOError):
                existing_links = []

        # Определяем новые ссылки (которых ещё нет в файле)
        existing_urls = {item['url'] for item in existing_links}
        new_links = [item for item in links_data if item['url'] not in existing_urls]
        combined = existing_links + new_links

        # Сохранение в JSON
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(combined, f, indent=4, ensure_ascii=False)

        # Сохранение списка URL
        with open(txt_file, 'w', encoding='utf-8') as f:
            for link in combined:
                f.write(f"{link['url']}\n")

        print(f"   [OK] Ссылки сохранены в: {json_file}")
        print(f"   [INFO] Новых ссылок добавлено: {len(new_links)} | Всего в файле: {len(combined)}")
