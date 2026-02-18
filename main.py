"""
Главный скрипт для парсинга вакансий с сайта rabota.by

Автор: ОАО "КЕРАМИН"
Версия: 2.0
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


def load_existing_data(output_file: str) -> list:
    """Загружает уже собранные вакансии из файла (или возвращает пустой список)"""
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            print(f"   [!] Не удалось прочитать существующий файл, начинаем заново")
            return []
    return []


def save_data(data: list, output_file: str):
    """Атомарно сохраняет данные: сначала во временный файл, потом переименовывает"""
    tmp_file = output_file + '.tmp'
    with open(tmp_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    shutil.move(tmp_file, output_file)


def main():
    """Основная функция запуска парсинга"""
    start_time = time.time()

    print("=" * 60)
    print("RABOTA.BY - Парсер вакансий v2.0")
    print("=" * 60)
    print()

    try:
        config = Config()
        cur_date = datetime.now().strftime("%m.%Y")
        output_file = config.get_data_file(f'data_finally_{cur_date}_Rabota_by.json')

        parser = VacancyParser(config)
        processor = DataProcessor(config)

        parser._init_driver()
        try:
            # Этап 1: Сбор ссылок на вакансии
            print("[+] Этап 1: Сбор ссылок на вакансии...")
            links_data = parser.collect_vacancy_links()

            if not links_data:
                print("[ERROR] Не удалось собрать ссылки на вакансии")
                return

            print(f"[OK] Собрано {len(links_data)} ссылок на вакансии\n")
            parser.save_links(links_data, cur_date)

            # Загружаем уже собранные вакансии и определяем, что ещё нужно собрать
            existing_data = load_existing_data(output_file)
            collected_urls = {v['url'] for v in existing_data}
            new_links = [l for l in links_data if l['url'] not in collected_urls]

            print(f"[INFO] Уже собрано: {len(existing_data)} вакансий")
            print(f"[INFO] Осталось собрать: {len(new_links)} вакансий\n")

            if not new_links:
                print("[OK] Все вакансии из этого месяца уже собраны")
            else:
                # Этап 2+3: Парсинг и обработка с немедленным сохранением
                print("[+] Этап 2-3: Парсинг, обработка и сохранение вакансий...")

                links_dict = {item['url']: item['specialization'] for item in links_data}
                total = len(new_links)
                failed = 0

                for idx, link_info in enumerate(new_links, 1):
                    url = link_info['url']

                    if idx % 10 == 0 or idx == total:
                        print(f"   [+] {idx}/{total} | В файле: {len(existing_data)} вакансий")

                    vacancy_data = parser.parse_vacancy_page(url)

                    if vacancy_data:
                        processed = processor.process_single_vacancy(vacancy_data, links_dict)
                        existing_data.append(processed)
                        save_data(existing_data, output_file)
                    else:
                        failed += 1

                print(f"\n[OK] Готово. Успешно: {total - failed}, не удалось: {failed}\n")

        finally:
            parser._close_driver()

        # Итоговая статистика
        print("=" * 60)
        print("[STAT] СТАТИСТИКА:")
        print(f"   Всего вакансий в файле: {len(existing_data)}")
        print(f"   Файл: data_finally_{cur_date}_Rabota_by.json")
        elapsed_time = round(time.time() - start_time, 2)
        print(f"   Время выполнения: {elapsed_time} секунд")
        print("=" * 60)
        print("\n[SUCCESS] Парсинг завершен успешно!")

    except KeyboardInterrupt:
        print("\n\n[!] Парсинг прерван пользователем")
        print("[INFO] Прогресс сохранён — при следующем запуске продолжится с того же места")
    except Exception as e:
        print(f"\n\n[ERROR] Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
