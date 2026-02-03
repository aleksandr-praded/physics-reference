# generate_presentation.py
import sqlite3
from jinja2 import Template
import argparse
import random
import os

def fix_latex_escapes(s):
    return "" if s is None else s.replace('\\\\', '\\')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--section", nargs='+')
    parser.add_argument("--school", nargs='+')
    parser.add_argument("--university", nargs='+')
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
        items.append({
            'type': 'formula',
            'name': f['name'],
            'content': fix_latex_escapes(f['formula_latex'])
        })

    cursor.execute("SELECT * FROM concepts ORDER BY section, subsection, name")
    for c in cursor.fetchall():
        if args.section and not any(s.lower() in c['section'].lower() for s in args.section): continue
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
                'duration': 1000 if item['type'] == 'formula' else 3000
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