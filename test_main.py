"""
ТЕСТОВАЯ версия парсера вакансий Rabota.by
Собирает только 1 страницу одного раздела и парсит 5 вакансий

Автор: ОАО "КЕРАМИН"
Версия: 2.0-TEST
"""

import sys
import os
import json
import shutil
import time
from datetime import datetime

# Добавляем src в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.parser import VacancyParser
from src.processor import DataProcessor
from src.config import Config

# Установка кодировки UTF-8 для Windows
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')


# Тестовые URL с известными зарплатами
SALARY_TEST_URLS = [
    {
        'url': 'https://rabota.by/vacancy/129935107?hhtmFrom=vacancy_search_list',
        'expected': 'от 2500 до 3000 Br на руки',
    },
    {
        'url': 'https://rabota.by/vacancy/129656778?hhtmFrom=vacancy_search_list',
        'expected': 'от 2500 Br на руки',
    },
    {
        'url': 'https://rabota.by/vacancy/117822686?hhtmFromLabel=employer_vacancy_tab&hhtmFrom=employer',
        'expected': 'до 3000 Br на руки',
    },
    {
        'url': 'https://rabota.by/vacancy/128473007?hhtmFromLabel=employer_vacancy_tab&hhtmFrom=employer',
        'expected': 'Уровень дохода не указан',
    },
]


def test_salary_extraction(parser):
    """
    Этап 0: тестирует извлечение зарплаты на 4 известных вакансиях.
    Выводит полученное значение рядом с ожидаемым.
    """
    from bs4 import BeautifulSoup
    import time as _time

    print("[+] Этап 0: Проверка извлечения зарплаты на тестовых вакансиях...")
    parser._init_driver()
    all_ok = True

    try:
        for i, item in enumerate(SALARY_TEST_URLS, 1):
            url = item['url']
            expected = item['expected']

            try:
                parser.driver.get(url)
                _time.sleep(2)
                soup = BeautifulSoup(parser.driver.page_source, 'lxml')
                salary = parser._extract_salary(soup)
                title = parser._extract_title(soup)

                status = '[OK]  ' if expected.lower() in salary.lower() else '[WARN]'
                if status == '[WARN]':
                    all_ok = False

                print(f"   {status} Вакансия {i}: {title[:50]}")
                print(f"          Получено : {salary}")
                print(f"          Ожидалось: {expected}")

            except Exception as e:
                all_ok = False
                print(f"   [ERROR] Вакансия {i} ({url[:60]}): {str(e)[:80]}")

    finally:
        parser._close_driver()

    if all_ok:
        print("[OK] Все зарплаты извлечены корректно\n")
    else:
        print("[WARN] Некоторые значения отличаются от ожидаемых — проверьте вывод выше\n")


def collect_test_links(parser, config):
    """
    Собирает ссылки только с ОДНОЙ страницы ОДНОЙ специализации.
    Драйвер должен быть уже инициализирован вызывающим кодом.

    Returns:
        List[Dict]: Список словарей {'Специализация': str, 'Ссылка': str}
    """
    links_data = []

    # Загружаем только первую ссылку и первую специализацию
    with open(config.LINKS_FILE, encoding='utf-8') as f:
        search_links = [
            line.strip() for line in f.readlines()
            if line.strip() and not line.strip().startswith('#')
        ]

    with open(config.NAMES_FILE, encoding='utf-8') as f:
        specializations = [
            line.strip() for line in f.readlines()
            if line.strip() and not line.strip().startswith('#')
        ]

    # Берем только первую специализацию
    search_link = search_links[0]
    spec_name = specializations[0]

    print(f"   [TEST] Специализация: {spec_name}")
    print(f"   [TEST] Парсим только ПЕРВУЮ страницу")

    # Открываем только первую страницу
    parser.driver.get(search_link)
    time.sleep(config.PARSER_CONFIG['delay_between_pages'])

    content = parser.driver.page_source
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(content, 'lxml')

    # Извлекаем ссылки только с первой страницы
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
        print(f"      [ERROR] Ошибка при сборе ссылок: {str(e)[:100]}")

    print(f"      [OK] Найдено ссылок: {len(links_data)}")

    return links_data


def parse_test_vacancies(parser, links_data, limit=5):
    """
    Парсит только первые N вакансий (по умолчанию 5)

    Args:
        parser: VacancyParser instance
        links_data: Список ссылок
        limit: Количество вакансий для парсинга

    Returns:
        List[Dict]: Список данных о вакансиях
    """
    parser._init_driver()
    vacancies = []

    try:
        # Берем только первые N ссылок
        test_links = links_data[:limit]
        total = len(test_links)

        print(f"   [TEST] Парсим только {total} вакансий")

        for idx, link_info in enumerate(test_links, 1):
            url = link_info['url']

            print(f"   [+] Обработка {idx}/{total}: {url[:60]}...")

            vacancy_data = parser.parse_vacancy_page(url)

            if vacancy_data:
                vacancies.append(vacancy_data)
                # print(f"      [OK] Вакансия успешно записана")
            else:
                print(f"      [ERROR] Не удалось спарсить вакансию")

    finally:
        parser._close_driver()

    return vacancies


def main():
    """Основная функция запуска ТЕСТОВОГО парсинга"""
    start_time = time.time()

    print("=" * 60)
    print("RABOTA.BY - Парсер вакансий v2.0 [ТЕСТОВАЯ ВЕРСИЯ]")
    print("=" * 60)
    print("[TEST] Ограничения:")
    print("   - 1 специализация")
    print("   - 1 страница поиска")
    print("   - 5 вакансий")
    print("=" * 60)
    print()

    try:
        config = Config()
        cur_date = datetime.now().strftime("%m.%Y")
        output_file = config.get_data_file(f'TEST_data_finally_{cur_date}_Rabota_by.json')
        TEST_LIMIT = 5

        parser = VacancyParser(config)
        processor = DataProcessor(config)

        parser._init_driver()
        try:
            # Этап 0: проверка извлечения зарплаты на 4 тестовых вакансиях
            # test_salary_extraction(parser)

            # Этап 1: Сбор ссылок (только 1 страница)
            print("[+] Этап 1: Сбор ссылок на вакансии (1 страница)...")
            links_data = collect_test_links(parser, config)

            if not links_data:
                print("[ERROR] Не удалось собрать ссылки на вакансии")
                return

            print(f"[OK] Собрано {len(links_data)} ссылок\n")

            # Сохранение ссылок
            json_file = config.get_data_file(f'TEST_links_{cur_date}_rabota_by.json')
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(links_data, f, indent=4, ensure_ascii=False)
            print(f"   [OK] Ссылки сохранены в: {json_file}\n")

            # Загружаем уже собранные тестовые данные
            existing_data = []
            if os.path.exists(output_file):
                try:
                    with open(output_file, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                except (json.JSONDecodeError, IOError):
                    existing_data = []

            collected_urls = {v['url'] for v in existing_data}
            new_links = [l for l in links_data[:TEST_LIMIT] if l['url'] not in collected_urls]

            print(f"[INFO] Уже собрано: {len(existing_data)} | Осталось: {len(new_links)}\n")

            # Этап 2+3: Парсинг и обработка с немедленным сохранением
            if not new_links:
                print("[OK] Все тестовые вакансии уже собраны")
            else:
                print(f"[+] Этап 2-3: Парсинг и обработка ({len(new_links)} вакансий)...")

                links_dict = {item['url']: item['specialization'] for item in links_data}

                for idx, link_info in enumerate(new_links, 1):
                    url = link_info['url']
                    print(f"   [+] {idx}/{len(new_links)}: {url[:60]}...")

                    vacancy_data = parser.parse_vacancy_page(url)
                    if vacancy_data:
                        processed = processor.process_single_vacancy(vacancy_data, links_dict)
                        existing_data.append(processed)
                        tmp = output_file + '.tmp'
                        with open(tmp, 'w', encoding='utf-8') as f:
                            json.dump(existing_data, f, indent=4, ensure_ascii=False)
                        shutil.move(tmp, output_file)
                        print(f"      [OK] Сохранено")
                    else:
                        print(f"      [ERROR] Не удалось спарсить")

        finally:
            parser._close_driver()

        # Статистика
        print("\n" + "=" * 60)
        print("[STAT] СТАТИСТИКА (ТЕСТ):")
        print(f"   Вакансий в файле: {len(existing_data)}")
        print(f"   Файл: TEST_data_finally_{cur_date}_Rabota_by.json")
        elapsed_time = round(time.time() - start_time, 2)
        print(f"   Время выполнения: {elapsed_time} секунд")
        print("=" * 60)
        print("\n[SUCCESS] Тестовый парсинг завершен успешно!")

    except KeyboardInterrupt:
        print("\n\n[!] Парсинг прерван пользователем")
        print("[INFO] Прогресс сохранён — при следующем запуске продолжится с того же места")
    except Exception as e:
        print(f"\n\n[ERROR] Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
