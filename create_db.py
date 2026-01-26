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

# === Таблица концепций (определения, правила) ===
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

# === Загрузка переменных из CSV ===
if os.path.exists('data/variables.csv'):
    with open('data/variables.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cursor.execute('''
                INSERT OR REPLACE INTO variables (key, symbol_latex, description_ru, unit)
                VALUES (?, ?, ?, ?)
            ''', (
                row['key'],
                row['symbol_latex'],
                row['description_ru'],
                row['unit']
            ))
    print("✅ Переменные загружены из data/variables.csv")
else:
    print("⚠️ Файл data/variables.csv не найден")

# === Загрузка формул из CSV ===
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
    print("✅ Формулы загружены из data/formulas.csv")
else:
    print("⚠️ Файл data/formulas.csv не найден")

# === Загрузка концепций из CSV ===
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
    print("✅ Концепции загружены из data/concepts.csv")
else:
    print("⚠️ Файл data/concepts.csv не найден")

conn.commit()
conn.close()
print("✅ База данных physics.db создана")