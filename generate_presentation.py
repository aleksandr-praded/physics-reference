# generate_presentation.py
import sqlite3
from jinja2 import Template
import argparse
import random
import os

def fix_latex_escapes(s):
    return "" if s is None else s.replace('\\\\', '\\')

def matches_level(db_level, allowed_school, allowed_univ):
    """
    Проверяет, соответствует ли запись фильтрам --school / --university.
    Примеры level: "school:7", "university:2"
    """
    if not db_level:
        return True  # если поле level пустое — пропускаем
    if ':' not in db_level:
        return True  # некорректный формат — пропускаем

    lvl_type, lvl_val = db_level.split(':', 1)
    try:
        lvl_num = int(lvl_val)
    except ValueError:
        return True  # не число — пропускаем

    # Преобразуем аргументы в строки для сравнения
    school_strs = [str(x) for x in (allowed_school or [])]
    univ_strs = [str(x) for x in (allowed_univ or [])]

    if allowed_school and lvl_type == 'school':
        return str(lvl_num) in school_strs
    if allowed_univ and lvl_type == 'university':
        return str(lvl_num) in univ_strs
    # Если фильтры не заданы — пропускаем запись
    return not allowed_school and not allowed_univ

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--section", nargs='+')
    parser.add_argument("--subsection", nargs='+')
    parser.add_argument("--school", nargs='+', type=int, help="Номера школьных классов (например: 7 8 9)")
    parser.add_argument("--university", nargs='+', type=int, help="Номера курсов (например: 1 2)")
    parser.add_argument("--limit", "-n", type=int, default=10, help="Количество вопросов в варианте")
    parser.add_argument("--variants", "-v", type=int, default=1, help="Количество вариантов")
    parser.add_argument("--output-prefix", type=str, default="presentation",
                        help="Префикс для имён файлов")
    args = parser.parse_args()

    # Загружаем данные один раз
    conn = sqlite3.connect('physics.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT key, symbol_latex, description_ru, unit FROM variables")
    variables_dict = {
        r['key']: {'symbol': fix_latex_escapes(r['symbol_latex']), 'desc': r['description_ru'], 'unit': r['unit']}
        for r in cursor.fetchall()
    }

    items = []
    cursor.execute("SELECT * FROM formulas ORDER BY section, subsection, name")
    for f in cursor.fetchall():
        if args.section and not any(s.lower() in f['section'].lower() for s in args.section): continue
        if args.subsection and not any(sb.lower() in f['subsection'].lower() for sb in args.subsection): continue
        if not matches_level(f['level'], args.school, args.university): continue
        items.append({
            'type': 'formula',
            'name': f['name'],
            'content': fix_latex_escapes(f['formula_latex'])
        })

    cursor.execute("SELECT * FROM concepts ORDER BY section, subsection, name")
    for c in cursor.fetchall():
        if args.section and not any(s.lower() in c['section'].lower() for s in args.section): continue
        if args.subsection and not any(sb.lower() in c['subsection'].lower() for sb in args.subsection): continue
        if not matches_level(c['level'], args.school, args.university): continue
        items.append({
            'type': 'concept',
            'name': c['name'],
            'content': c['definition']
        })
    conn.close()

    if not items:
        print("⚠️ Нет данных, удовлетворяющих фильтрам")
        return

    # Генерация вариантов
    for var_num in range(1, args.variants + 1):
        # Копируем и перемешиваем
        pool = items.copy()
        random.shuffle(pool)
        selected = pool[:args.limit]

        # === Сохраняем список ответов ===
        quiz_file = f"{args.output_prefix}_variant_{var_num}.txt"
        with open(quiz_file, 'w', encoding='utf-8') as f_list:
            f_list.write(f"Вариант {var_num}\n\n")
            for i, item in enumerate(selected, 1):
                f_list.write(f"{i}. {item['name']}\n")
                if item['type'] == 'formula':
                    f_list.write(f"   Ответ: ${item['content']}$\n\n")
                else:
                    f_list.write(f"   Ответ: {item['content']}\n\n")

        # === Генерация HTML ===
        slides = []
        for i, item in enumerate(selected, 1):
            slides.append({
                'number': i,
                'name': item['name'],
                'duration': 10_000 if item['type'] == 'formula' else 30_000
            })

        with open('templates/presentation.html', 'r', encoding='utf-8') as f_html:
            template = Template(f_html.read())
        html = template.render(slides=slides, variant_number=var_num)

        html_file = f"{args.output_prefix}_variant_{var_num}.html"
        with open(html_file, 'w', encoding='utf-8') as f_html:
            f_html.write(html)

        print(f"✅ Вариант {var_num}: {html_file}, {quiz_file}")

if __name__ == "__main__":
    main()