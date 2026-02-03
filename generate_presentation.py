# generate_presentation.py
import sqlite3
from jinja2 import Template
import argparse
import random

def fix_latex_escapes(s):
    return "" if s is None else s.replace('\\\\', '\\')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--section", nargs='+')
    parser.add_argument("--school", nargs='+')
    parser.add_argument("--university", nargs='+')
    parser.add_argument("--limit", "-n", type=int, help="Максимальное количество слайдов")
    parser.add_argument("--output-list", "-o", type=str, default="presentation_list.txt",
                        help="Файл для сохранения списка вопросов и ответов")
    args = parser.parse_args()

    conn = sqlite3.connect('physics.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT key, symbol_latex, description_ru, unit FROM variables")
    variables_dict = {
        r['key']: {'symbol': fix_latex_escapes(r['symbol_latex']), 'desc': r['description_ru'], 'unit': r['unit']}
        for r in cursor.fetchall()
    }

    # Загружаем все записи в один список
    items = []
    cursor.execute("SELECT * FROM formulas ORDER BY section, subsection, name")
    for f in cursor.fetchall():
        if args.section and not any(s.lower() in f['section'].lower() for s in args.section): continue
        items.append({
            'type': 'formula',
            'name': f['name'],
            'content': fix_latex_escapes(f['formula_latex']),
            'sources': []  # можно добавить, если нужно
        })

    cursor.execute("SELECT * FROM concepts ORDER BY section, subsection, name")
    for c in cursor.fetchall():
        if args.section and not any(s.lower() in c['section'].lower() for s in args.section): continue
        items.append({
            'type': 'concept',
            'name': c['name'],
            'content': c['definition'],
            'sources': []
        })

    # Случайный выбор
    if args.limit is not None:
        random.shuffle(items)
        items = items[:args.limit]

    # === Сохраняем список с ответами ===
    with open(args.output_list, 'w', encoding='utf-8') as f_list:
        for i, item in enumerate(items, 1):
            f_list.write(f"{i}. {item['name']}\n")
            if item['type'] == 'formula':
                f_list.write(f"   Ответ: ${item['content']}$\n\n")
            else:
                f_list.write(f"   Ответ: {item['content']}\n\n")

    # === Генерация HTML ===
    with open('templates/presentation.html', 'r', encoding='utf-8') as f_html:
        template = Template(f_html.read())
    html = template.render(slides=items)  # ← передаём ЕДИНЫЙ список

    with open('presentation.html', 'w', encoding='utf-8') as f_html:
        f_html.write(html)

    print(f"✅ Презентация: presentation.html ({len(items)} слайдов)")
    print(f"✅ Список с ответами: {args.output_list}")

if __name__ == "__main__":
    main()