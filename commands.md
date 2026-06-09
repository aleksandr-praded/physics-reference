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

SEARCH_TERM = "Фазовые переходы. Насыщенный пар"
output_file = "output_list.txt"

# Очистка/создание файла
with open(output_file, "w", encoding="utf-8") as f_out:
    f_out.write("")

def extract_from_csv(filepath, subsection_col_idx):
    found = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) > subsection_col_idx and SEARCH_TERM in row[subsection_col_idx]:
                found.append(f'"{row[0]}"')
    return found

# Индексы: concepts -> subsection в колонке 3, formulas -> в колонке 4
all_names = extract_from_csv("data/concepts.csv", 3) + extract_from_csv("data/formulas.csv", 4)

with open(output_file, "a", encoding="utf-8") as f_out:
    f_out.write("\n".join(all_names))
```

## Command Line

### 1. Открытие всех файлов в отдельных окнах
Открыть файл с указанным расширением в указанном браузере
```cmd
for %i in (*.html) do start msedge "%cd%%i" --new-window
```

## Power Shell

### 1. Открытие всех файлов в отдельных окнах
Открыть файл с указанным расширением в указанном браузере
```powershell
Get-ChildItem *.html | ForEach-Object { Start-Process chrome "--new-window `"$($_.FullName)`"" }
```

## Bash

### 1. Быстрая проверка структуры CSV (Python one-liner)
Проверка csv-файлов на наличие требуемой структуры
```bash
python -c "import csv; [print(row) for row in csv.reader(open('data/concepts.csv', encoding='utf-8')) if row]"
```