# Парсинг всех вакансий в г. Минске на сайте rabota.by

Парсер вакансий с [rabota.by](https://rabota.by) для мониторинга рынка труда Беларуси. Собирает данные по всем **174 специализациям**, гармонизирует их и сохраняет в JSON для дальнейшего анализа и визуализации.

---

## Что собирает парсер

Для каждой вакансии извлекается **26 полей**:

| Поле | Описание |
|---|---|
| `title` | Название вакансии |
| `salary_raw` | Сырое значение зарплаты с сайта |
| `salary_min` / `salary_max` | Числовые значения зарплаты |
| `salary_avg` | Средняя зарплата, округленная до 50 |
| `currency` | BYN, USD, EUR |
| `salary_type` | На руки / До вычета |
| `experience` | Опыт работы (исходное значение) |
| `experience_harmonized` | Без опыта / 1-3 года / 3-6 лет / Более 6 лет |
| `work_schedule` | График работы (исходное значение) |
| `employment_type` | Полная / Частичная / Проектная / Стажировка |
| `work_format` | Формат работы (исходное значение) |
| `company` | Название компании |
| `address` | Полный адрес |
| `city` | Извлеченный город (Минск, Гомель и т.д.) |
| `description` | Полный текст описания вакансии |
| `skills` | Требуемые навыки, через `;` |
| `skills_count` | Числовое количество навыков |
| `specialization` | Профессиональная роль |
| `specialization_category` | IT / Продажи / Производство / ... |
| `specialist_level` | Директор / Руководитель / Ведущий / Специалист / ... |
| `company_vacancy` | Комбинированное поле для визуализации |
| `has_salary` | `true` / `false` |
| `remote_work` | `true` / `false` |
| `description_length` | Количество символов в описании |
| `url` | URL вакансии на rabota.by |
| `monitoring_date` / `monitoring_time` | Дата и время сбора |

---

## Структура проекта

```
RabotaBy/
├── main.py                  # Основной скрипт запуска
├── test_main.py             # Быстрая проверка (5 вакансий, ~2 мин)
├── requirements.txt
│
├── src/
│   ├── parser.py            # Сбор данных с rabota.by
│   ├── processor.py         # Обработка и обогащение записей
│   ├── harmonization.py     # 8 функций гармонизации данных
│   └── config.py            # Параметры парсера и Chrome
│
├── config/
│   ├── search_links.txt     # все 174 ссылки поиска по специализациям
│   ├── specializations.txt  # все 174 названия специализаций
│   └── README.md            # Как настроить свои специализации
│
├── docs/
│   └── examples/
│       └── sample_data.json # Пример выходного JSON
│
└── data/                    # Сюда сохраняются результаты (в .gitignore)
```

---

## Установка

**Требования:** Python 3.8+, Google Chrome

```bash
git clone https://github.com/your-username/RabotaBy.git
cd RabotaBy
pip install -r requirements.txt
```

---

## Запуск

### Быстрая проверка (рекомендуется перед полным запуском)

```bash
python test_main.py
```

Парсит **1 специализацию, 1 страницу, 5 вакансий**. Занимает ~1-2 минуты. Результат сохраняется с префиксом `TEST_` в папке `data/`.

### Полный запуск

```bash
python main.py
```

Парсит все 174 специализации. Процесс можно прерывать — при следующем запуске уже собранные вакансии пропускаются.

---

## Выходные файлы

После запуска в папке `data/` появляются:

| Файл | Описание |
|---|---|
| `data_finally_MM.YYYY_Rabota_by.json` | Основной файл с обработанными вакансиями |
| `links_and_names_MM.YYYY_rabota_by.json` | Все собранные ссылки со специализациями |
| `url_list_MM.YYYY_RabotaBy.txt` | Список URL (по одному на строку) |

---

## Гармонизация данных

Модуль `src/harmonization.py` приводит сырые данные к аналитическому стандарту:

**`harmonize_specialist_level(title)`** — определяет разряд по названию вакансии:
- Директор → Руководитель → Главный специалист → Ведущий специалист → Стажер → Специалист

**`harmonize_experience(experience)`** — нормализует опыт:
- `"от 3 до 6 лет"` → `"3-6 лет"`

**`harmonize_employment_type(employment)`** — нормализует занятость:
- `"Полная занятость"`, `"Частичная занятость"`, `"Проектная работа"`, `"Стажировка"`

**`harmonize_work_schedule(schedule)`** — нормализует график:
- `"Полный день"`, `"Сменный"`, `"Гибкий"`, `"Удаленная работа"`

**`extract_salary_range(salary_str)`** — структурирует зарплату:
```python
{
    'min': 2500,
    'max': 4000,
    'currency': 'BYN',
    'type': 'На руки'   # или 'До вычета'
}
```
Поддерживает диапазоны, одно значение, BYN/USD/EUR/RUB. Зарплата "до вычета" автоматически пересчитывается в нетто (×0.85).

**`get_average_salary(min, max)`** — средняя зарплата, округленная до 50.

**`harmonize_city(address)`** — извлекает город из адреса (22 белорусских города).

**`classify_specialization_category(specialization)`** — определяет категорию:
- IT и технологии, Продажи и маркетинг, Производство, Строительство, Финансы, Медицина, Транспорт, Образование, Административная работа

---

## Использование для визуализации

Выходной JSON готов к загрузке в **Power BI**, **Tableau**, **Excel Power Query** или в Python (pandas, plotly).

### Пример загрузки в pandas

```python
import pandas as pd

df = pd.read_json('data/data_finally_02.2026_Rabota_by.json')

# Топ-10 навыков по частоте
skills = df['skills'].dropna().str.split('; ').explode()
print(skills.value_counts().head(10))

# Медианная зарплата по категориям специализаций
print(df.groupby('specialization_category')['salary_min'].median())

# Доля вакансий с удаленной работой
print(df['remote_work'].value_counts(normalize=True))
```

### Ключевые поля для дашбордов

| Задача | Поля |
|---|---|
| Анализ зарплат | `salary_min`, `salary_max`, `salary_avg`, `currency` |
| Карта вакансий | `city` |
| Структура рынка | `specialization_category`, `specialist_level` |
| Популярные навыки | `skills`, `skills_count` |
| Формат работы | `remote_work`, `employment_type` |
| Фильтр по компании | `company_vacancy` |

---

## Технологии

- **[undetected-chromedriver](https://github.com/ultrafunkamsterdam/undetected-chromedriver)** — обход антибот-защиты
- **[Selenium](https://selenium.dev)** — автоматизация браузера
- **[BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/)** + **lxml** — парсинг HTML
- **Python stdlib**: `json`, `re`, `datetime`, `pathlib`

---

## Особенности

- **Инкрементальное сохранение** — процесс можно прерывать и продолжать, уже собранные вакансии пропускаются
- **Атомарная запись** — данные сначала пишутся во временный файл, затем переименовываются (защита от повреждения при прерывании)
- **Обход защиты** — undetected-chromedriver автоматически обходит детектирование бота на rabota.by
- **174 специализации** — полное покрытие рынка по профессиональным ролям

---

## Решение проблем

**`ModuleNotFoundError`**
```bash
pip install -r requirements.txt
```

**ChromeDriver не запускается**
Убедитесь, что Google Chrome установлен. undetected-chromedriver определяет версию автоматически. Чтобы указать вручную, в `src/config.py` измените значение `'chrome_version'`.

**Timeout при загрузке страницы**
Увеличьте в `src/config.py`:
```python
'timeout': 60,
'delay_between_requests': 0.5,
```

---

## Лицензия

MIT License — свободное использование в коммерческих и некоммерческих целях.
