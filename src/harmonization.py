"""
Модуль гармонизации данных для вакансий с rabota.by
Приводит различные вариации значений к единому стандарту
"""

from typing import Optional


# ============= ГАРМОНИЗАЦИЯ РАЗРЯДА СПЕЦИАЛИСТА =============

def harmonize_specialist_level(vacancy_title: str) -> str:
    """
    Гармонизация разряда специалиста по названию вакансии

    Категории:
    - Директор/Руководитель
    - Главный специалист
    - Ведущий специалист
    - Специалист/Рабочий
    - Стажер/Помощник
    """
    if not vacancy_title:
        return 'Не указано'

    title_lower = vacancy_title.lower()

    # Высший уровень
    if any(word in title_lower for word in ['директор', 'генеральный', 'исполнительный']):
        return 'Директор'

    # Руководящий состав
    if any(word in title_lower for word in ['начальник', 'руководитель', 'заведующий']):
        return 'Руководитель'

    # Главные специалисты
    if any(word in title_lower for word in ['главный']):
        return 'Главный специалист'

    # Ведущие специалисты
    if any(word in title_lower for word in ['ведущий', 'старший', 'senior']):
        return 'Ведущий специалист'

    # Стажеры и помощники
    if any(word in title_lower for word in ['стажер', 'помощник', 'младший', 'junior', 'ассистент']):
        return 'Стажер/Помощник'

    # По умолчанию
    return 'Специалист/Рабочий'


# ============= ГАРМОНИЗАЦИЯ ОПЫТА РАБОТЫ =============

def harmonize_experience(experience: str) -> str:
    """
    Гармонизация опыта работы

    Стандарт:
    - Без опыта
    - 1-3 года
    - 3-6 лет
    - Более 6 лет
    """
    if not experience or experience == 'Error':
        return 'Не указано'

    exp_lower = experience.lower()

    if 'без опыта' in exp_lower or 'не требуется' in exp_lower:
        return 'Без опыта'

    if '1' in exp_lower or '2' in exp_lower or '3' in exp_lower:
        if 'от 3' not in exp_lower:
            return '1-3 года'

    if 'от 3' in exp_lower or '3–6' in exp_lower or '3-6' in exp_lower:
        return '3-6 лет'

    if 'более 6' in exp_lower or 'от 6' in exp_lower:
        return 'Более 6 лет'

    return experience


# ============= ГАРМОНИЗАЦИЯ ТИПА ЗАНЯТОСТИ =============

def harmonize_employment_type(employment: str) -> str:
    """
    Гармонизация типа занятости

    Стандарт:
    - Полная занятость
    - Частичная занятость
    - Проектная работа
    - Стажировка
    - Волонтерство
    """
    if not employment or employment == 'Error':
        return 'Не указано'

    emp_lower = employment.lower()

    if 'полная' in emp_lower or 'полный день' in emp_lower:
        return 'Полная занятость'

    if 'частичная' in emp_lower or 'неполный' in emp_lower or 'по совместительству' in emp_lower:
        return 'Частичная занятость'

    if 'проект' in emp_lower:
        return 'Проектная работа'

    if 'стажировка' in emp_lower:
        return 'Стажировка'

    if 'волонтер' in emp_lower:
        return 'Волонтерство'

    return employment


# ============= ГАРМОНИЗАЦИЯ ГРАФИКА РАБОТЫ =============

def harmonize_work_schedule(schedule: str) -> str:
    """
    Гармонизация графика работы

    Стандарт:
    - Полный день
    - Сменный график
    - Гибкий график
    - Удаленная работа
    """
    if not schedule or schedule == 'Error':
        return 'Не указано'

    sched_lower = schedule.lower()

    if 'полный день' in sched_lower:
        return 'Полный день'

    if 'сменный' in sched_lower or 'посменно' in sched_lower:
        return 'Сменный график'

    if 'гибкий' in sched_lower or 'свободный' in sched_lower:
        return 'Гибкий график'

    if 'удален' in sched_lower or 'remote' in sched_lower:
        return 'Удаленная работа'

    return schedule


# ============= ИЗВЛЕЧЕНИЕ ЗАРПЛАТЫ =============

def extract_salary_range(salary_str: str) -> dict:
    """
    Извлекает диапазон зарплаты из строки

    Возвращает:
    {
        'min': минимальная зарплата (int или None),
        'max': максимальная зарплата (int или None),
        'currency': валюта ('BYN', 'USD', 'EUR', и т.д.),
        'type': тип ('на руки', 'до вычета', 'не указано')
    }
    """
    result = {
        'min': None,
        'max': None,
        'currency': 'Не указано',
        'type': 'Не указано'
    }

    if not salary_str or salary_str == 'Error':
        return result

    # Определение валюты
    if 'br' in salary_str.lower() or 'руб' in salary_str.lower() or 'р.' in salary_str.lower():
        result['currency'] = 'BYN'
    elif '$' in salary_str or 'usd' in salary_str.lower():
        result['currency'] = 'USD'
    elif '€' in salary_str or 'eur' in salary_str.lower():
        result['currency'] = 'EUR'

    # Определение типа
    if 'на руки' in salary_str.lower():
        result['type'] = 'На руки'
    elif 'до вычета' in salary_str.lower():
        result['type'] = 'До вычета'

    # Извлечение чисел
    import re
    numbers = re.findall(r'\d+(?:\s?\d+)*', salary_str)
    numbers = [int(n.replace(' ', '')) for n in numbers]

    salary_lower = salary_str.lower()

    if len(numbers) >= 2:
        result['min'] = min(numbers[0], numbers[1])
        result['max'] = max(numbers[0], numbers[1])
    elif len(numbers) == 1:
        if 'до' in salary_lower:
            # "до 2500" — только максимум
            result['max'] = numbers[0]
        elif 'от' in salary_lower:
            # "от 2500" — только минимум
            result['min'] = numbers[0]
        else:
            # "2500 руб." — фиксированная сумма
            result['min'] = numbers[0]
            result['max'] = numbers[0]

    # Если зарплата указана "до вычета налогов" — пересчитываем в нетто (×0.85)
    if result['type'] == 'До вычета':
        if result['min'] is not None:
            result['min'] = round(result['min'] * 0.85)
        if result['max'] is not None:
            result['max'] = round(result['max'] * 0.85)

    return result


def get_average_salary(min_salary: Optional[int], max_salary: Optional[int]) -> Optional[int]:
    """
    Возвращает среднюю зарплату, округлённую до 50 руб.

    - Диапазон (min + max): среднее арифметическое, округлённое до 50
    - Одно значение: возвращает его, округлённое до 50
    - Нет данных: возвращает None
    """
    if min_salary is None and max_salary is None:
        return None

    if min_salary is not None and max_salary is not None:
        avg = (min_salary + max_salary) / 2
    elif min_salary is not None:
        avg = min_salary
    else:
        avg = max_salary

    # Округление до ближайших 50 (0.5 всегда вверх)
    return int((avg + 25) / 50) * 50


# ============= ГАРМОНИЗАЦИЯ ГОРОДА =============

def harmonize_city(address: str) -> str:
    """
    Извлекает и гармонизирует название города из адреса
    """
    if not address or address == 'Error':
        return 'Не указано'

    addr_lower = address.lower()

    # Основные города Беларуси
    cities_mapping = {
        'минск': 'Минск',
        'гомель': 'Гомель',
        'могилев': 'Могилёв',
        'могилёв': 'Могилёв',
        'витебск': 'Витебск',
        'гродно': 'Гродно',
        'брест': 'Брест',
        'бобруйск': 'Бобруйск',
        'барановичи': 'Барановичи',
        'борисов': 'Борисов',
        'пинск': 'Пинск',
        'мозырь': 'Мозырь',
        'солигорск': 'Солигорск',
        'лида': 'Лида',
        'молодечно': 'Молодечно',
        'полоцк': 'Полоцк',
        'жлобин': 'Жлобин',
        'светлогорск': 'Светлогорск',
        'речица': 'Речица',
        'жодино': 'Жодино',
        'слуцк': 'Слуцк',
        'новополоцк': 'Новополоцк'
    }

    for city_key, city_name in cities_mapping.items():
        if city_key in addr_lower:
            return city_name

    # Если город не найден, пытаемся извлечь первое слово
    words = address.split(',')
    if words:
        return words[0].strip()

    return 'Не указано'


# ============= КЛАССИФИКАЦИЯ СПЕЦИАЛИЗАЦИИ =============

def classify_specialization_category(specialization: str) -> str:
    """
    Классифицирует специализацию по широким категориям

    Категории:
    - IT и технологии
    - Продажи и маркетинг
    - Производство
    - Административная работа
    - Строительство
    - Финансы и бухгалтерия
    - Образование
    - Медицина
    - Транспорт и логистика
    - Другое
    """
    if not specialization or specialization == 'Не указано':
        return 'Другое'

    spec_lower = specialization.lower()

    # IT и технологии
    if any(word in spec_lower for word in ['программист', 'разработ', 'it', 'developer', 'тестиров', 'devops', 'администратор', 'аналитик данных']):
        return 'IT и технологии'

    # Продажи и маркетинг
    if any(word in spec_lower for word in ['продаж', 'маркетинг', 'менеджер по', 'торговый', 'pr', 'реклам']):
        return 'Продажи и маркетинг'

    # Производство
    if any(word in spec_lower for word in ['производств', 'инженер', 'технолог', 'оператор', 'слесарь', 'токарь']):
        return 'Производство'

    # Административная работа
    if any(word in spec_lower for word in ['секретар', 'офис', 'администратор', 'делопроизводств', 'hr', 'кадр']):
        return 'Административная работа'

    # Строительство
    if any(word in spec_lower for word in ['строит', 'прораб', 'монтаж', 'отделочник', 'электрик', 'сантехник']):
        return 'Строительство'

    # Финансы и бухгалтерия
    if any(word in spec_lower for word in ['бухгалтер', 'финанс', 'экономист', 'аудит', 'банк']):
        return 'Финансы и бухгалтерия'

    # Образование
    if any(word in spec_lower for word in ['преподават', 'учитель', 'воспитател', 'педагог', 'методист']):
        return 'Образование'

    # Медицина
    if any(word in spec_lower for word in ['врач', 'медицин', 'медсестра', 'фельдшер', 'фармацевт']):
        return 'Медицина'

    # Транспорт и логистика
    if any(word in spec_lower for word in ['водитель', 'логист', 'экспедитор', 'грузчик', 'курьер', 'транспорт']):
        return 'Транспорт и логистика'

    return 'Другое'
