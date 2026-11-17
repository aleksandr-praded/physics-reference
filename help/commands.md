    
# 📖 Справочник полезных команд

> 💡 **Как использовать:** Скопируйте нужный блок и вставьте в терминал, консоль Python или сохраните как отдельный скрипт. Все пути относительны корню проекта.

## Python

### 1. Форматирование строк в CSV-формат
Преобразует plain-text список в готовые CSV-строки для импорта. Первые 8 строк → концепции, остальные → формулы.
```python
with open('output.txt', 'r', encoding='utf-8') as f1:
    all_lines = f1.readlines()

concepts = [
    f'"{line.strip()}","pass","Электричество и магнетизм","Электрические колебания. Электромагнитные волны","university:2","",""'
    for line in all_lines[:8]
]
formulas = [
    f'"{line.strip()}","pass","electric_charge","Электричество и магнетизм","Электрические колебания. Электромагнитные волны","university:2","",""'
    for line in all_lines[8:]
]

with open('output_concepts.txt', 'w', encoding='utf-8') as f2:
    print(*concepts, sep='\n', file=f2)

with open('output_formulas.txt', 'w', encoding='utf-8') as f3:
    print(*formulas, sep='\n', file=f3)
```
### 2. Извлечение названий подразделов из .tex
Парсит сгенерированный LaTeX-файл и собирает все \subsection{...} в текстовый список
```python
with open('6.tex', 'r', encoding='utf-8') as f:
    # Безопасный парсинг: извлекаем текст между { и }
    names = [
        f'"{line.split("{")[1].split("}")[0]}"'
        for line in f
        if "subsection" in line and "{" in line
    ]

with open('output_list.txt', 'w', encoding='utf-8') as f_out:
    print(*names[1:], sep='\n', file=f_out)  # [1:] пропускает заголовок документа
```
### 3. Выборка названий из csv по ключевому слову
Ищет записи в concepts.csv, formulas.csv, где подраздел содержит заданную фразу
```python
import csv
import os
from pathlib import Path

SEARCH_TERM = 'Электрические явления'
KEY_TO_COLUMN = {'concepts': 2, 'variables': 3}

def extract_from_csv(filepath: Path, column: int):
    found = []
    with open(filepath, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) > column and SEARCH_TERM.lower() in row[column].lower():
                name = row[0].strip()
                if name:
                    found.append(f'"{name}"')
    return found

all_names = []
for dirpath, dirnames, filenames in os.walk(os.getcwd()):
    # Проверяем, что путь содержит physics_docs/data как компоненты, а не подстроку
    parts = Path(dirpath).parts
    if 'physics_docs' not in parts or 'data' not in parts:
        continue
    # Убеждаемся, что data идёт сразу после physics_docs (или где-то после)
    try:
        idx = parts.index('physics_docs')
        if parts[idx + 1] != 'data':
            continue
    except (ValueError, IndexError):
        continue

    for filename in filenames:
        path = Path(filename)
        if path.suffix != '.csv':
            continue
        column = KEY_TO_COLUMN.get(path.stem)
        if column is None:
            continue
        all_names.extend(extract_from_csv(Path(dirpath) / filename, column))

unique_names = list(dict.fromkeys(all_names))
with open('output.txt', 'w', encoding='utf-8', newline='') as f:
    f.write(' '.join(unique_names))
```

## Command Line

### 1. Открытие всех файлов в отдельных окнах
Открыть файл с указанным расширением в указанном браузере
```cmd
for %i in (*.html) do start msedge "%cd%%i" --new-window
```

### 2. Компиляция листингов, содержащих русские символы
Необходимо использовать Пайтон-пакет Pygments для успешного создания файла
```cmd
pdflatex --shell-escape ваш_файл.tex
```

## Power Shell

### 1. Открытие всех файлов в отдельных окнах
Открыть файл с указанным расширением в указанном браузере
```powershell
Get-ChildItem *.html | ForEach-Object { Start-Process chrome "--new-window `"$($_.FullName)`"" }
```

### 2. Открытие файлов, содержащих определённую строку
Ищет файлы, содержащие определённую строку, и открывает их в выбранном приложении в разных окнах
```powershell
Get-ChildItem -Recurse -File | Where-Object {$_.FullName -like "*ЕГФ*5-6*.txt"} | Select-String "кинетическая энергия" | Select-Object -Property Path -Unique | ForEach-Object {Start-Process notepad $_.Path}
```

## Bash

### 1. Быстрая проверка структуры CSV (Python one-liner)
Проверка csv-файлов на наличие требуемой структуры
```bash
python -c "import csv; [print(row) for row in csv.reader(open('data/concepts.csv', encoding='utf-8')) if row]"
```