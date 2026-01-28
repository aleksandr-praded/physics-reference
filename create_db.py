# create_db.py
import sqlite3
import csv
import os

if os.path.exists('physics.db'):
    os.remove('physics.db')
    print("✅ Старая база удалена")

os.makedirs('data', exist_ok=True)

conn = sqlite3.connect('physics.db')
cursor = conn.cursor()

# === Таблица формул ===
cursor.execute('''
CREATE TABLE IF NOT EXISTS formulas (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    formula_latex TEXT NOT NULL,
    variable_keys TEXT NOT NULL,
    section TEXT NOT NULL,
    subsection TEXT NOT NULL,
    level TEXT,
    image_path TEXT
)
''')

# === Таблица концепций ===
cursor.execute('''
CREATE TABLE IF NOT EXISTS concepts (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    definition TEXT NOT NULL,
    section TEXT NOT NULL,
    subsection TEXT NOT NULL,
    level TEXT,
    image_path TEXT
)
''')

# === Таблица переменных ===
cursor.execute('''
CREATE TABLE IF NOT EXISTS variables (
    id INTEGER PRIMARY KEY,
    key TEXT UNIQUE NOT NULL,
    symbol_latex TEXT NOT NULL,
    description_ru TEXT NOT NULL,
    unit TEXT
)
''')

# === Таблица источников ===
cursor.execute('''
CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY,
    citation TEXT NOT NULL,
    comment TEXT
)
''')

# === Связи: формулы ↔ источники ===
cursor.execute('''
CREATE TABLE IF NOT EXISTS formula_sources (
    formula_id INTEGER,
    source_id INTEGER,
    FOREIGN KEY(formula_id) REFERENCES formulas(id),
    FOREIGN KEY(source_id) REFERENCES sources(id)
)
''')

# === Связи: концепции ↔ источники ===
cursor.execute('''
CREATE TABLE IF NOT EXISTS concept_sources (
    concept_id INTEGER,
    source_id INTEGER,
    FOREIGN KEY(concept_id) REFERENCES concepts(id),
    FOREIGN KEY(source_id) REFERENCES sources(id)
)
''')

# === Загрузка переменных ===
if os.path.exists('data/variables.csv'):
    with open('data/variables.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cursor.execute('''
                INSERT OR REPLACE INTO variables (key, symbol_latex, description_ru, unit)
                VALUES (?, ?, ?, ?)
            ''', (row['key'], row['symbol_latex'], row['description_ru'], row['unit']))
    print("✅ Переменные загружены")
else:
    print("⚠️ variables.csv не найден")

# === Загрузка источников ===
if os.path.exists('data/sources.csv'):
    with open('data/sources.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cursor.execute('''
                INSERT OR REPLACE INTO sources (id, citation, comment)
                VALUES (?, ?, ?)
            ''', (int(row['id']), row['citation'], row.get('comment', '')))
    print("✅ Источники загружены")
else:
    print("⚠️ sources.csv не найден")

# === Вспомогательная функция: найти ID по имени ===
def get_formula_id(name):
    cursor.execute("SELECT id FROM formulas WHERE name = ?", (name,))
    res = cursor.fetchone()
    return res[0] if res else None

def get_concept_id(name):
    cursor.execute("SELECT id FROM concepts WHERE name = ?", (name,))
    res = cursor.fetchone()
    return res[0] if res else None

# === Загрузка формул ===
if os.path.exists('data/formulas.csv'):
    with open('data/formulas.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            image_path = row['image_path'].strip() if row.get('image_path') else None
            cursor.execute('''
                INSERT OR REPLACE INTO formulas 
                (name, formula_latex, variable_keys, section, subsection, level, image_path)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                row['name'],
                row['formula_latex'],
                row['variable_keys'],
                row['section'],
                row['subsection'],
                row.get('level', ''),
                image_path
            ))
    print("✅ Формулы загружены")
else:
    print("⚠️ formulas.csv не найден")

# === Загрузка связей формул с источниками ===
if os.path.exists('data/formula_sources.csv'):
    with open('data/formula_sources.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            formula_id = get_formula_id(row['formula_name'])
            if formula_id:
                source_ids = [int(x.strip()) for x in row['source_ids'].split(',') if x.strip()]
                for sid in source_ids:
                    cursor.execute('''
                        INSERT OR REPLACE INTO formula_sources (formula_id, source_id)
                        VALUES (?, ?)
                    ''', (formula_id, sid))
    print("✅ Связи формул с источниками загружены")
else:
    print("⚠️ formula_sources.csv не найден")

# === Загрузка концепций ===
if os.path.exists('data/concepts.csv'):
    with open('data/concepts.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            image_path = row['image_path'].strip() if row.get('image_path') else None
            cursor.execute('''
                INSERT OR REPLACE INTO concepts 
                (name, definition, section, subsection, level, image_path)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                row['name'],
                row['definition'],
                row['section'],
                row['subsection'],
                row.get('level', ''),
                image_path
            ))
    print("✅ Концепции загружены")
else:
    print("⚠️ concepts.csv не найден")

# === Загрузка связей концепций с источниками ===
if os.path.exists('data/concept_sources.csv'):
    with open('data/concept_sources.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            concept_id = get_concept_id(row['concept_name'])
            if concept_id:
                source_ids = [int(x.strip()) for x in row['source_ids'].split(',') if x.strip()]
                for sid in source_ids:
                    cursor.execute('''
                        INSERT OR REPLACE INTO concept_sources (concept_id, source_id)
                        VALUES (?, ?)
                    ''', (concept_id, sid))
    print("✅ Связи концепций с источниками загружены")
else:
    print("⚠️ concept_sources.csv не найден")

conn.commit()
conn.close()
print("✅ База данных physics.db создана")